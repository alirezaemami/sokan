"""A self-hosted, proof-of-work captcha (compatible with the ALTCHA scheme).

The server picks a secret number, hashes it with a random salt and signs the
hash. The browser has to find that number by brute force, which takes a person's
device under a second but makes scripted sign-ups and password guessing
expensive. Nothing is loaded from a third party, so it works where Google and
Cloudflare are unreliable, and there are no keys to manage.

A solution is accepted once: its signature is remembered until it expires.

Sign-in goes through Frappe's own /api/method/login; the `before_login` hook
below checks the solution there. Desk users (Administrator, System Users) are
exempt, so Desk sign-in keeps working; Frappe's login lockout protects them.
"""

import base64
import hashlib
import hmac
import json
import secrets
import time

import frappe
from frappe import _

ALGORITHM = "SHA-256"
# Average work is half of this: ~0.1 s on a laptop, 1-3 s on a slow phone (it runs
# while the person types). Raise it in site_config (sokan_captcha_max_number) under attack.
DEFAULT_MAX_NUMBER = 300_000
TTL = 10 * 60


class CaptchaError(frappe.ValidationError):
	http_status_code = 417


def _secret() -> bytes:
	from frappe.utils.password import get_encryption_key

	return hashlib.sha256(f"sokan-captcha:{get_encryption_key()}".encode()).digest()


def _sign(challenge: str) -> str:
	return hmac.new(_secret(), challenge.encode(), hashlib.sha256).hexdigest()


def _hash(salt: str, number: int) -> str:
	return hashlib.sha256(f"{salt}{number}".encode()).hexdigest()


def disabled() -> bool:
	return bool(frappe.flags.in_test or frappe.conf.get("sokan_captcha_disabled"))


def create_challenge() -> dict:
	max_number = frappe.utils.cint(frappe.conf.get("sokan_captcha_max_number")) or DEFAULT_MAX_NUMBER
	salt = f"{secrets.token_hex(12)}?expires={int(time.time()) + TTL}"
	number = secrets.randbelow(max_number + 1)
	challenge = _hash(salt, number)
	return {
		"algorithm": ALGORITHM,
		"challenge": challenge,
		"maxnumber": max_number,
		"salt": salt,
		"signature": _sign(challenge),
	}


def verify(payload: str | None):
	"""Throw CaptchaError unless `payload` is a fresh, unused solution."""
	if disabled():
		return
	failed = _("Please confirm you're not a robot and try again.")
	try:
		data = json.loads(base64.b64decode(payload or ""))
		salt, challenge, signature = str(data["salt"]), str(data["challenge"]), str(data["signature"])
		number = int(data["number"])
		expires = int(salt.rsplit("?expires=", 1)[1])
	except Exception:
		frappe.throw(failed, CaptchaError)

	if (
		data.get("algorithm") != ALGORITHM
		or expires < time.time()
		or not hmac.compare_digest(_sign(challenge), signature)
		or not hmac.compare_digest(_hash(salt, number), challenge)
	):
		frappe.throw(failed, CaptchaError)

	# One use per solution. SET NX is atomic, so two parallel requests can't both pass.
	key = frappe.cache.make_key(f"sokan:captcha-used:{signature}")
	if not frappe.cache.set(key, 1, ex=TTL + 60, nx=True):
		frappe.throw(failed, CaptchaError)


def before_login(login_manager=None):
	"""Hook: require a solved captcha for website sign-ins."""
	if disabled():
		return
	usr = (frappe.form_dict.get("usr") or "").strip()
	if usr == "Administrator" or (
		usr and frappe.db.get_value("User", {"name": usr.lower()}, "user_type") == "System User"
	):
		return
	verify(frappe.form_dict.get("captcha"))
