"""Sign-up, identity and password recovery.

Sign-in and sign-out use Frappe's own endpoints (/api/method/login, logout);
sokan.captcha.before_login checks the captcha on sign-in. Sign-up, email
verification, "who am I" and the password reset flow live here, so every email
uses the Sokan template and every link points at the website, not Desk.
"""

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.sessions import get_csrf_token

from sokan import verification
from sokan.captcha import create_challenge
from sokan.captcha import verify as verify_captcha
from sokan.utils import (
	ROLE_ADMIN,
	ROLE_CUSTOMER,
	ROLE_FORWARDER,
	customer_for_user,
	forwarder_for_user,
)


def request_language() -> str:
	"""The site language the visitor is using (the frontend sends it as Accept-Language)."""
	header = (frappe.request.headers.get("Accept-Language") if frappe.request else "") or ""
	return "fa" if header.lower().startswith("fa") else "en"


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
			# Emails go out in the language they signed up in.
			"language": request_language(),
			"roles": [{"role": role}],
		}
	)
	user.flags.ignore_permissions = True
	user.insert()
	return user


def _login(user: str):
	frappe.local.login_manager.login_as(user)


def _check_captcha(payload: str | None):
	verify_captcha(payload)


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
	captcha: str | None = None,
):
	_check_captcha(captcha)
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
	# The welcome email waits until the address is confirmed.
	verification.send_code(user.name)
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
	captcha: str | None = None,
):
	_check_captcha(captcha)
	modes = frappe.parse_json(modes) if isinstance(modes, str) else (modes or [])
	valid_modes = set(frappe.get_all("Sokan Transport Mode", {"is_active": 1}, pluck="name"))
	modes = [m for m in modes if m in valid_modes]
	if not modes:
		frappe.throw(_("Choose at least one transport mode you handle."))
	if not (company_name or "").strip():
		frappe.throw(_("Company name is required."))

	user = _create_user(email, full_name, password, phone, ROLE_FORWARDER)
	fwd = frappe.get_doc(
		{
			"doctype": "Sokan Forwarder",
			"company_name": company_name.strip(),
			"email": user.name,
			"phone": phone,
			"country": country,
			"city": city,
			"website": website,
			"license_number": license_number,
			# Pending until the email is confirmed; verification.on_verified then
			# auto-approves it or puts it in front of the managers.
			"status": "Pending",
			"services": [{"transport_mode": m} for m in modes],
			"members": [{"user": user.name, "member_role": "Owner"}],
		}
	)
	fwd.flags.awaiting_email_verification = True
	fwd.insert(ignore_permissions=True)
	_login(user.name)
	verification.send_code(user.name)
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
		"email_verified": verification.is_verified(user),
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


# --------------------------------------------------------------------------- passwords


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=5, seconds=60 * 60)
def forgot_password(email: str, captcha: str | None = None):
	"""Email a reset link to the website. Always answers the same way, so it can't
	be used to find out which addresses have accounts."""
	_check_captcha(captcha)
	email = (email or "").strip().lower()
	user = frappe.db.get_value("User", {"name": email, "enabled": 1}, "name")
	# Managers set up in Desk are System Users; the link goes to their inbox either way.
	if user and user not in ("Administrator", "Guest"):
		link = frappe.get_doc("User", user)._reset_password(send_email=False)
		key = link.split("key=", 1)[1].split("&", 1)[0]
		seconds = frappe.utils.cint(frappe.get_system_settings("reset_password_link_expiry_duration")) or 1200
		from sokan.notifications import notify_password_reset

		notify_password_reset(user, key, max(seconds // 60, 1))
	return {"ok": True}


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=10, seconds=60 * 60)
def reset_password(key: str, new_password: str):
	"""Set a new password from an emailed link, sign the user in and confirm by email."""
	from frappe.core.doctype.user.user import update_password

	result = update_password(new_password=new_password, logout_all_sessions=1, key=key)
	if frappe.local.response.get("http_status_code") == 410:
		# Expired or already used: update_password returns the reason.
		frappe.throw(
			result or _("This reset link has expired. Please request a new one."), frappe.LinkExpired
		)
	user = frappe.session.user
	# The reset link was emailed, so following it proves the address.
	verification.mark_verified(user)
	from sokan.notifications import notify_password_changed

	notify_password_changed(user)
	return me()


# --------------------------------------------------------------------------- captcha + verification


@frappe.whitelist(allow_guest=True, methods=["GET"])
@rate_limit(limit=120, seconds=10 * 60)
def captcha_challenge():
	return create_challenge()


@frappe.whitelist(methods=["POST"])
@rate_limit(limit=10, seconds=60 * 60)
def send_verification_code(force: int = 0):
	"""Email the signed-in user a code. `force` is the Resend button."""
	user = frappe.session.user
	if verification.is_verified(user):
		return {"verified": True}
	return {
		"verified": False,
		"email": user,
		**verification.send_code(user, force=bool(frappe.utils.cint(force))),
	}


@frappe.whitelist(methods=["POST"])
@rate_limit(limit=30, seconds=60 * 60)
def verify_email(code: str):
	verification.check_code(frappe.session.user, code)
	return me()
