import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now_datetime


class SokanTopUp(Document):
	"""A forwarder's request to add credit. Approving it posts the wallet transaction."""

	def validate(self):
		if flt(self.amount) <= 0:
			frappe.throw(_("Top-up amount must be greater than zero."))
		# Always the wallet's currency. Never trust a pre-filled value: Frappe fills empty
		# "currency" fields from the site default, which needn't match the wallet.
		self.currency = (
			frappe.db.get_value("Sokan Forwarder", self.forwarder, "wallet_currency") or self.currency
		)
		before = self.get_doc_before_save()
		if before and before.status == "Approved" and self.status != "Approved":
			frappe.throw(_("An approved top-up cannot be reopened. Post an Adjustment instead."))

	def on_update(self):
		if self.status in ("Approved", "Rejected") and not self.reviewed_on:
			self.db_set({"reviewed_by": frappe.session.user, "reviewed_on": now_datetime()})

		if self.status == "Approved" and not self.wallet_transaction:
			from sokan.billing import post

			txn = post(
				self.forwarder,
				"Top-up",
				self.amount,
				reference=self,
				description=_("{0} — {1}").format(self.payment_method, self.payment_reference or self.name),
			)
			self.db_set("wallet_transaction", txn.name)
			from sokan.notifications import notify_topup

			notify_topup(self)
		elif self.status == "Rejected" and self.has_value_changed("status"):
			from sokan.notifications import notify_topup

			notify_topup(self)
