"""Forwarder billing.

Sokan is prepaid: a forwarder tops up a wallet and Sokan debits it for

* unlocking a request (seeing the full shipment and the customer's contact) and
* submitting a quote on it,

plus an optional monthly plan fee. Each plan can include a number of free
unlocks / quotes per calendar month before fees apply.

Every balance change is a Sokan Wallet Transaction; its controller locks the
forwarder row, so two concurrent debits can never both spend the same credit.
"""

import frappe
from frappe import _
from frappe.utils import add_months, flt, get_first_day, getdate, now_datetime, nowdate

from sokan.utils import get_settings, platform_currency


class InsufficientBalance(frappe.ValidationError):
	pass


def fees_for(forwarder) -> frappe._dict:
	"""Effective fees for a forwarder: plan values, falling back to platform defaults."""
	settings = get_settings()
	plan = frappe.get_cached_doc("Sokan Plan", forwarder.plan) if forwarder.plan else None
	return frappe._dict(
		view_fee=flt(plan.view_fee) if plan and plan.view_fee else flt(settings.default_view_fee),
		quote_fee=flt(plan.quote_fee) if plan and plan.quote_fee else flt(settings.default_quote_fee),
		free_views=int(plan.free_views_per_month or 0) if plan else 0,
		free_quotes=int(plan.free_quotes_per_month or 0) if plan else 0,
		monthly_fee=flt(plan.monthly_fee) if plan else 0,
		currency=(plan.currency if plan else None) or platform_currency(),
	)


def _current_period() -> str:
	return nowdate()[:7]


def _lock_forwarder(name: str):
	"""Re-read the forwarder under a row lock; callers decide what to charge from this copy."""
	frappe.db.sql("select name from `tabSokan Forwarder` where name=%s for update", name)
	doc = frappe.get_doc("Sokan Forwarder", name)
	if doc.usage_period != _current_period():
		doc.usage_period = _current_period()
		doc.free_views_used = 0
		doc.free_quotes_used = 0
		doc.db_update()
	return doc


def post(forwarder: str, transaction_type: str, amount: float, *, reference=None, description=None):
	"""Insert a ledger line. Raises InsufficientBalance for an uncovered debit."""
	txn = frappe.get_doc(
		{
			"doctype": "Sokan Wallet Transaction",
			"forwarder": forwarder,
			"transaction_type": transaction_type,
			"amount": flt(amount, 2),
			"reference_doctype": reference.doctype if reference else None,
			"reference_name": reference.name if reference else None,
			"description": description,
		}
	)
	txn.insert(ignore_permissions=True)
	return txn


def _charge(forwarder_name: str, kind: str, reference, description: str) -> frappe._dict:
	"""Charge one unlock or quote, using the free allowance first.

	Returns {fee, was_free, transaction}.
	"""
	fwd = _lock_forwarder(forwarder_name)
	fees = fees_for(fwd)
	used_field, allowance, fee = (
		("free_views_used", fees.free_views, fees.view_fee)
		if kind == "unlock"
		else ("free_quotes_used", fees.free_quotes, fees.quote_fee)
	)

	if int(fwd.get(used_field) or 0) < allowance:
		frappe.db.set_value("Sokan Forwarder", fwd.name, used_field, int(fwd.get(used_field) or 0) + 1)
		return frappe._dict(fee=0, was_free=1, transaction=None)

	if fee <= 0:
		return frappe._dict(fee=0, was_free=0, transaction=None)

	if flt(fwd.wallet_balance) < fee:
		frappe.throw(
			_("Your wallet balance ({0}) does not cover this {1} fee of {2}. Please top up.").format(
				frappe.format_value(fwd.wallet_balance, {"fieldtype": "Currency", "options": fees.currency}),
				_("unlock") if kind == "unlock" else _("quote"),
				frappe.format_value(fee, {"fieldtype": "Currency", "options": fees.currency}),
			),
			InsufficientBalance,
			title=_("Insufficient balance"),
		)

	txn = post(
		fwd.name,
		"Request Unlock" if kind == "unlock" else "Quote Fee",
		-fee,
		reference=reference,
		description=description,
	)
	return frappe._dict(fee=fee, was_free=0, transaction=txn.name)


def charge_unlock(lead) -> frappe._dict:
	return _charge(lead.forwarder, "unlock", lead, _("Unlocked request {0}").format(lead.request))


def charge_quote(quote) -> frappe._dict:
	return _charge(quote.forwarder, "quote", quote, _("Quote on request {0}").format(quote.request))


def grant_signup_bonus(forwarder):
	bonus = flt(get_settings().signup_bonus)
	if bonus <= 0:
		return
	if frappe.db.exists(
		"Sokan Wallet Transaction", {"forwarder": forwarder.name, "transaction_type": "Signup Bonus"}
	):
		return
	post(forwarder.name, "Signup Bonus", bonus, description=_("Welcome credit"))


def refund(lead, reason: str) -> float:
	"""Credit back an unlock fee, e.g. when the customer cancels right after publishing. Returns the amount refunded."""
	if not lead.wallet_transaction or not flt(lead.unlock_fee):
		return 0
	if frappe.db.exists(
		"Sokan Wallet Transaction",
		{"reference_doctype": lead.doctype, "reference_name": lead.name, "transaction_type": "Refund"},
	):
		return 0
	post(lead.forwarder, "Refund", flt(lead.unlock_fee), reference=lead, description=reason)
	return flt(lead.unlock_fee)


def charge_subscriptions():
	"""Monthly: debit each active forwarder's plan fee. A forwarder who can't pay drops to the default plan."""
	today = getdate()
	default_plan = frappe.db.get_value("Sokan Plan", {"is_default": 1, "is_active": 1}, "name")
	for row in frappe.get_all(
		"Sokan Forwarder",
		filters={"status": "Active", "plan": ("is", "set")},
		fields=["name", "plan", "plan_renews_on"],
	):
		if row.plan_renews_on and getdate(row.plan_renews_on) > today:
			continue
		fee = flt(frappe.db.get_value("Sokan Plan", row.plan, "monthly_fee"))
		next_renewal = add_months(get_first_day(today), 1)
		from sokan.notifications import notify_plan_downgraded, notify_plan_renewed

		try:
			if fee > 0:
				post(
					row.name,
					"Subscription",
					-fee,
					description=_("{0} plan — {1}").format(row.plan, today.strftime("%B %Y")),
				)
			frappe.db.set_value("Sokan Forwarder", row.name, "plan_renews_on", next_renewal)
			frappe.db.commit()
			if fee > 0:
				notify_plan_renewed(row.name, row.plan, fee, today.strftime("%B %Y"))
		except InsufficientBalance:
			frappe.db.rollback()
			if default_plan and default_plan != row.plan:
				frappe.db.set_value(
					"Sokan Forwarder", row.name, {"plan": default_plan, "plan_renews_on": next_renewal}
				)
				frappe.db.commit()
				notify_plan_downgraded(row.name, row.plan, default_plan, fee)
		frappe.db.commit()


def wallet_summary(forwarder) -> dict:
	fees = fees_for(forwarder)
	period = _current_period()
	same_period = forwarder.usage_period == period
	views_used = int(forwarder.free_views_used or 0) if same_period else 0
	quotes_used = int(forwarder.free_quotes_used or 0) if same_period else 0
	return {
		"balance": flt(forwarder.wallet_balance),
		"currency": fees.currency,
		"plan": forwarder.plan,
		"plan_renews_on": forwarder.plan_renews_on,
		"view_fee": fees.view_fee,
		"quote_fee": fees.quote_fee,
		"monthly_fee": fees.monthly_fee,
		"free_views_left": max(fees.free_views - views_used, 0),
		"free_quotes_left": max(fees.free_quotes - quotes_used, 0),
		"low_balance": flt(forwarder.wallet_balance) < flt(get_settings().low_balance_threshold),
		"as_of": str(now_datetime()),
	}
