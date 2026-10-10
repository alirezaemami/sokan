"""Email verification with a 6-digit code.

Sign-up signs the person in straight away, but until they type the code we
emailed them, their address is unproven:

- shippers can fill in a request, but it stays a draft until they verify;
- a forwarder's application stays out of the managers' queue (and isn't
  auto-approved) until they verify;
- welcome emails wait for verification, so an address someone mistyped only
  ever receives the code.

The code lives in Redis, hashed, for 15 minutes and allows 5 guesses. The
verified flag is a custom field on User (`sokan_email_verified`). Desk users
and managers are always treated as verified.
"""

import hashlib
import hmac
import json
import secrets
import time

import frappe
from frappe import _

from sokan.utils import ROLE_ADMIN

FIELD = "sokan_email_verified"
CODE_TTL = 15 * 60
RESEND_AFTER = 60
MAX_ATTEMPTS = 5

# Persian and Arabic-Indic digits, as phone keyboards type them.
_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


class EmailNotVerified(frappe.ValidationError):
	http_status_code = 403


class VerificationCodeError(frappe.ValidationError):
	"""Wrong code. The response says how many guesses are left."""


class VerificationCodeExpired(frappe.ValidationError):
	"""No live code: it expired, was used up, or was never sent."""


def custom_fields() -> dict:
	return {
		"User": [
			{
				"fieldname": FIELD,
				"label": "Email Verified (Sokan)",
				"fieldtype": "Check",
				"insert_after": "email",
				"read_only": 1,
				"no_copy": 1,
				"default": "0",
			}
		]
	}


def make_custom_fields():
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

	create_custom_fields(custom_fields(), update=True)


def is_verified(user: str | None = None) -> bool:
	user = user or frappe.session.user
	if user == "Guest":
		return False
	if user == "Administrator":
		return True
	row = frappe.db.get_value("User", user, ["user_type", FIELD], as_dict=True)
	if not row:
		return False
	if row.get(FIELD) or row.user_type == "System User":
		return True
	return ROLE_ADMIN in frappe.get_roles(user)


def require_verified(user: str | None = None):
	if not is_verified(user):
		frappe.throw(_("Please verify your email address first."), EmailNotVerified)


# --------------------------------------------------------------------------- codes


def _key(user: str) -> str:
	return frappe.cache.make_key(f"sokan:email-code:{user}")


def _digest(user: str, code: str) -> str:
	from frappe.utils.password import get_encryption_key

	return hmac.new(get_encryption_key().encode(), f"{user}:{code}".encode(), hashlib.sha256).hexdigest()


def _state(user: str) -> dict | None:
	raw = frappe.cache.get(_key(user))
	return json.loads(raw) if raw else None


def send_code(user: str, force: bool = False) -> dict:
	"""Email a fresh code, unless a recent one is still usable.

	Without `force` (page load) a live code is never replaced, so refreshing the
	page doesn't flood the inbox. With `force` (the Resend button) a new code goes
	out once RESEND_AFTER has passed since the last one.
	"""
	now = time.time()
	state = _state(user)
	if state:
		wait = int(state["sent"] + RESEND_AFTER - now)
		if not force or wait > 0:
			return {"sent": False, "resend_in": max(wait, 0)}

	code = f"{secrets.randbelow(10**6):06d}"
	frappe.cache.set(
		_key(user),
		json.dumps({"digest": _digest(user, code), "sent": now, "attempts": 0}),
		ex=CODE_TTL,
	)
	from sokan.notifications import notify_verification_code

	notify_verification_code(user, code, CODE_TTL // 60)
	return {"sent": True, "resend_in": RESEND_AFTER}


def check_code(user: str, code: str):
	"""Mark `user` verified if `code` matches; otherwise throw."""
	state = _state(user)
	if not state or state["attempts"] >= MAX_ATTEMPTS:
		frappe.throw(
			_("This code has expired or was used up. Send yourself a new one."), VerificationCodeExpired
		)

	code = "".join(ch for ch in (code or "").translate(_DIGITS) if ch.isdigit())
	if not hmac.compare_digest(state["digest"], _digest(user, code)):
		state["attempts"] += 1
		frappe.cache.set(_key(user), json.dumps(state), keepttl=True)
		left = MAX_ATTEMPTS - state["attempts"]
		frappe.local.response["attempts_left"] = left
		frappe.throw(_("That code isn't right. {0} tries left.").format(left), VerificationCodeError)

	frappe.cache.delete(_key(user))
	mark_verified(user)


def mark_verified(user: str, announce: bool = True):
	"""Record a proven address, then do what sign-up held back."""
	if frappe.db.get_value("User", user, FIELD):
		return
	frappe.db.set_value("User", user, FIELD, 1, update_modified=False)
	if announce:
		on_verified(user)


def on_verified(user: str):
	from sokan.notifications import (
		notify_admin_new_forwarder,
		notify_welcome_forwarder,
		notify_welcome_shipper,
	)
	from sokan.utils import customer_for_user, forwarder_for_user, get_settings

	if customer_for_user(user, required=False):
		notify_welcome_shipper(user, frappe.utils.get_fullname(user))

	fwd_name = forwarder_for_user(user, required=False)
	if not fwd_name:
		return
	fwd = frappe.get_doc("Sokan Forwarder", fwd_name)
	if fwd.status != "Pending":
		return
	if get_settings().auto_approve_forwarders:
		# Activation sends the approval email, grants the welcome credit and hands over open requests.
		fwd.status = "Active"
		fwd.save(ignore_permissions=True)
	else:
		notify_welcome_forwarder(fwd)
		notify_admin_new_forwarder(fwd)
