"""Plans store their customer-facing text in the database, so the
Shipper -> Customer / Forwarder -> Provider rename has to reach existing rows too.

Only the visible text (plan description and feature lines) is rewritten.
"""

import re

import frappe

WORDS = [
	(r"\bForwarders\b", "Providers"),
	(r"\bForwarder\b", "Provider"),
	(r"\bforwarders\b", "providers"),
	(r"\bforwarder\b", "provider"),
	(r"\bShippers\b", "Customers"),
	(r"\bShipper\b", "Customer"),
	(r"\bshippers\b", "customers"),
	(r"\bshipper\b", "customer"),
]


def _swap(text: str) -> str:
	for pattern, repl in WORDS:
		text = re.sub(pattern, repl, text)
	return text


def execute():
	for doctype, field in (("Sokan Plan", "description"), ("Sokan Plan Feature", "feature")):
		for row in frappe.get_all(doctype, fields=["name", field]):
			old = row.get(field) or ""
			new = _swap(old)
			if new != old:
				frappe.db.set_value(doctype, row.name, field, new, update_modified=False)
