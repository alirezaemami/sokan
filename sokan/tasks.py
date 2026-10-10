"""Scheduled jobs (wired in hooks.scheduler_events)."""

import frappe
from frappe.utils import nowdate


def expire_requests():
	"""Daily: close requests whose quoting window has passed."""
	for name in frappe.get_all(
		"Freight Request", {"status": "Open", "valid_until": ("<", nowdate())}, pluck="name"
	):
		doc = frappe.get_doc("Freight Request", name)
		doc.status = "Expired"
		doc.flags.ignore_permissions = True
		doc.save()
		frappe.db.commit()
		from sokan.notifications import notify_request_expired

		notify_request_expired(name)


def expire_quotes():
	"""Daily: a quote past its validity can no longer be accepted."""
	frappe.db.set_value(
		"Freight Quote", {"status": "Submitted", "valid_until": ("<", nowdate())}, "status", "Expired"
	)


def charge_subscriptions():
	from sokan.billing import charge_subscriptions as run

	run()


def admin_digest():
	"""Daily: tell managers what's waiting for them (skipped when nothing is)."""
	from sokan.notifications import send_admin_digest

	send_admin_digest()
