"""Sign-up and identity.

Sign-in, sign-out and password reset use Frappe's own endpoints
(/api/method/login, /api/method/logout, reset_password); these add the two
Sokan-specific sign-ups and a single "who am I" call the frontend boots from.
"""

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.sessions import get_csrf_token

from sokan.utils import (
	ROLE_ADMIN,
	ROLE_CUSTOMER,
	ROLE_FORWARDER,
	customer_for_user,
	forwarder_for_user,
	get_settings,
)


def _create_user(email: str, full_name: str, password: str, phone: str | None, role: str):
	email = (email or "").strip().lower()
	frappe.utils.validate_email_address(email, throw=True)
	if frappe.db.exists("User", email):
		frappe.throw(
			_("An account with this email already exists. Please sign in instead."),
			frappe.DuplicateEntryError,
		)
	if len(password or "") < 8:
		frappe.throw(_("Password must be at least 8 characters."))

	first, _sep, last = (full_name or "").strip().partition(" ")
	user = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": first or email.split("@")[0],
			"last_name": last,
			"mobile_no": phone,
			"user_type": "Website User",
			"send_welcome_email": 0,
			"new_password": password,
			"roles": [{"role": role}],
		}
	)
	user.flags.ignore_permissions = True
	user.insert()
	return user


def _login(user: str):
	frappe.local.login_manager.login_as(user)


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=10, seconds=60 * 60)
def register_customer(
	full_name: str,
	email: str,
	password: str,
	phone: str | None = None,
	company_name: str | None = None,
	country: str | None = None,
	customer_type: str = "Business",
):
	user = _create_user(email, full_name, password, phone, ROLE_CUSTOMER)
	frappe.get_doc(
		{
			"doctype": "Sokan Customer",
			"user": user.name,
			"full_name": full_name,
			"email": user.name,
			"phone": phone,
			"company_name": company_name,
			"country": country or None,
			"customer_type": "Individual" if customer_type == "Individual" else "Business",
		}
	).insert(ignore_permissions=True)
	_login(user.name)
	return me()


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=5, seconds=60 * 60)
def register_forwarder(
	company_name: str,
	full_name: str,
	email: str,
	password: str,
	phone: str,
	country: str,
	city: str | None = None,
	website: str | None = None,
	modes: list[str] | str | None = None,
	license_number: str | None = None,
):
	modes = frappe.parse_json(modes) if isinstance(modes, str) else (modes or [])
	valid_modes = set(frappe.get_all("Sokan Transport Mode", {"is_active": 1}, pluck="name"))
	modes = [m for m in modes if m in valid_modes]
	if not modes:
		frappe.throw(_("Choose at least one transport mode you handle."))
	if not (company_name or "").strip():
		frappe.throw(_("Company name is required."))

	user = _create_user(email, full_name, password, phone, ROLE_FORWARDER)
	auto = get_settings().auto_approve_forwarders
	frappe.get_doc(
		{
			"doctype": "Sokan Forwarder",
			"company_name": company_name.strip(),
			"email": user.name,
			"phone": phone,
			"country": country,
			"city": city,
			"website": website,
			"license_number": license_number,
			"status": "Active" if auto else "Pending",
			"services": [{"transport_mode": m} for m in modes],
			"members": [{"user": user.name, "member_role": "Owner"}],
		}
	).insert(ignore_permissions=True)
	_login(user.name)
	return me()


@frappe.whitelist(allow_guest=True, methods=["GET"])
def me():
	user = frappe.session.user
	if user == "Guest":
		return {"user": None}

	roles = set(frappe.get_roles(user))
	data = {
		"user": user,
		"full_name": frappe.utils.get_fullname(user),
		"image": frappe.db.get_value("User", user, "user_image"),
		"is_admin": ROLE_ADMIN in roles or "System Manager" in roles,
		# Session-cookie POSTs must echo this back as X-Frappe-CSRF-Token.
		"csrf_token": get_csrf_token(),
		"customer": None,
		"forwarder": None,
	}
	if cust := customer_for_user(user, required=False):
		data["customer"] = frappe.db.get_value(
			"Sokan Customer", cust, ["name", "full_name", "company_name", "is_blocked"], as_dict=True
		)
	if fwd := forwarder_for_user(user, required=False):
		data["forwarder"] = frappe.db.get_value(
			"Sokan Forwarder",
			fwd,
			["name", "company_name", "slug", "status", "logo", "wallet_balance", "wallet_currency"],
			as_dict=True,
		)
	return data


@frappe.whitelist(methods=["POST"])
def become_customer(company_name: str | None = None, phone: str | None = None):
	"""Let a signed-in forwarder (or any user) also request quotes as a shipper."""
	if customer_for_user(required=False):
		return me()
	frappe.get_doc(
		{
			"doctype": "Sokan Customer",
			"user": frappe.session.user,
			"full_name": frappe.utils.get_fullname(frappe.session.user),
			"email": frappe.session.user,
			"phone": phone,
			"company_name": company_name,
		}
	).insert(ignore_permissions=True)
	return me()
