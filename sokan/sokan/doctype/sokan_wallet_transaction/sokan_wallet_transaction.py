import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now_datetime

DEBIT_TYPES = {"Request Unlock", "Quote Fee", "Subscription"}
CREDIT_TYPES = {"Top-up", "Signup Bonus", "Refund"}


class SokanWalletTransaction(Document):
	"""Immutable wallet ledger line. Inserting one is the only way the balance changes."""

	def validate(self):
		if not self.is_new():
			frappe.throw(_("Wallet transactions cannot be edited. Post an Adjustment instead."))
		self.amount = flt(self.amount, 2)
		if not self.amount:
			frappe.throw(_("Amount cannot be zero."))
		if self.transaction_type in DEBIT_TYPES and self.amount > 0:
			self.amount = -self.amount
		if self.transaction_type in CREDIT_TYPES and self.amount < 0:
			frappe.throw(_("{0} must be a positive amount.").format(_(self.transaction_type)))

	def before_insert(self):
		from sokan.billing import InsufficientBalance
		from sokan.utils import platform_currency

		# Row lock: concurrent postings for one forwarder serialize here.
		balance, currency = frappe.db.sql(
			"select wallet_balance, wallet_currency from `tabSokan Forwarder` where name=%s for update",
			self.forwarder,
		)[0]
		new_balance = flt(balance) + self.amount
		if self.amount < 0 and self.transaction_type != "Adjustment" and new_balance < -0.005:
			frappe.throw(_("Insufficient wallet balance."), InsufficientBalance)

		self.balance_before = flt(balance, 2)
		self.balance_after = flt(new_balance, 2)
		self.currency = currency or platform_currency()
		self.posting_date = now_datetime()
		frappe.db.set_value(
			"Sokan Forwarder",
			self.forwarder,
			{"wallet_balance": self.balance_after, "wallet_currency": self.currency},
			update_modified=False,
		)

	def after_insert(self):
		# Warn once, at the moment a debit takes the wallet below the threshold.
		threshold = flt(frappe.db.get_single_value("Sokan Settings", "low_balance_threshold"))
		if threshold and self.amount < 0 and flt(self.balance_before) >= threshold > flt(self.balance_after):
			from sokan.notifications import notify_low_balance

			notify_low_balance(self.forwarder)

	def on_trash(self):
		frappe.throw(_("Wallet transactions cannot be deleted. Post an Adjustment instead."))
