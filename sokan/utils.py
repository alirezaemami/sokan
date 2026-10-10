"""Shared helpers: settings, identity resolution and small formatting utilities."""

import re

import frappe
from frappe import _

ROLE_ADMIN = "Sokan Admin"
ROLE_FORWARDER = "Sokan Forwarder"
ROLE_CUSTOMER = "Sokan Customer"


def get_settings():
	return frappe.get_cached_doc("Sokan Settings")


def platform_currency() -> str:
	return get_settings().default_currency or "USD"


def slugify(text: str) -> str:
	slug = re.sub(r"[^\w\s-]", "", (text or "").lower(), flags=re.UNICODE)
	slug = re.sub(r"[\s_-]+", "-", slug).strip("-")
	return slug[:80] or frappe.generate_hash(length=8)


def unique_slug(doctype: str, text: str, name: str | None = None) -> str:
	base = slugify(text)
	slug, n = base, 1
	while frappe.db.exists(doctype, {"slug": slug, "name": ("!=", name or "")}):
		n += 1
		slug = f"{base}-{n}"
	return slug


def require_login():
	if frappe.session.user == "Guest":
		frappe.throw(_("Please sign in to continue."), frappe.AuthenticationError)


def forwarder_for_user(user: str | None = None, *, required: bool = True) -> str | None:
	"""The Sokan Forwarder the user acts for, via the company's Members table."""
	user = user or frappe.session.user
	name = frappe.db.get_value(
		"Sokan Forwarder Member", {"user": user, "parenttype": "Sokan Forwarder"}, "parent"
	)
	if not name and required:
		frappe.throw(_("Your account is not linked to a forwarder company."), frappe.PermissionError)
	return name


def active_forwarder_for_user(user: str | None = None):
	"""The forwarder doc, refusing companies that are not yet active."""
	name = forwarder_for_user(user)
	doc = frappe.get_doc("Sokan Forwarder", name)
	if doc.status != "Active":
		frappe.throw(
			_("Your company is {0}. You can browse requests once it is approved.").format(_(doc.status)),
			frappe.PermissionError,
		)
	return doc


def customer_for_user(user: str | None = None, *, required: bool = True) -> str | None:
	user = user or frappe.session.user
	name = frappe.db.get_value("Sokan Customer", {"user": user}, "name")
	if not name and required:
		frappe.throw(_("Your account has no customer profile."), frappe.PermissionError)
	return name


def add_role(user: str, role: str):
	if not frappe.db.exists("Has Role", {"parent": user, "role": role, "parenttype": "User"}):
		u = frappe.get_doc("User", user)
		u.flags.ignore_permissions = True
		u.add_roles(role)


def frontend_url(path: str = "") -> str:
	base = (get_settings().frontend_url or frappe.utils.get_url()).rstrip("/")
	return f"{base}/{path.lstrip('/')}" if path else base


def file_url(path: str | None) -> str | None:
	"""Frappe file paths are served by the frontend's /files proxy, so relative is fine."""
	return path or None
