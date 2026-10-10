"""bench commands for Sokan.

bench --site sokan.local sokan-add-manager you@example.com --name "Your Name"
    Creates the first manager (or grants the role to an existing user).
    Further managers can be added from the admin portal's Settings → Managers.

bench --site sokan.local sokan-check
    Go-live check: settings, email, money and access, with what to fix.
"""

import click
from frappe.commands import get_site, pass_context


@click.command("sokan-add-manager")
@click.argument("email")
@click.option("--name", "full_name", default=None, help="Full name for a new account.")
@pass_context
def add_manager(context, email, full_name=None):
	"""Give EMAIL access to the Sokan admin portal (/admin)."""
	import frappe

	frappe.init(site=get_site(context))
	frappe.connect()
	try:
		frappe.set_user("Administrator")
		from sokan.api.admin import add_manager as grant

		grant(email, full_name)
		frappe.db.commit()
		click.echo(f"{email} can now sign in to /admin. New accounts get an email to set a password.")
	finally:
		frappe.destroy()


def run_checks() -> list[tuple[str, str, str]]:
	"""(level, check, detail) for everything that must be right before real users arrive."""
	import frappe
	from frappe.utils import cint, flt
	from frappe.utils.scheduler import is_scheduler_disabled

	from sokan.utils import ROLE_ADMIN

	out = []

	def check(ok, name, fix, level="FAIL"):
		out.append(("OK" if ok else level, name, "" if ok else fix))

	s = frappe.get_single("Sokan Settings")
	url = (s.frontend_url or "").strip()
	check(
		url.startswith("https://"),
		"Website address (Sokan Settings → Frontend URL)",
		f"is '{url or 'empty'}'. Set it to the public https URL; every email link and the email logo use it.",
	)
	check(
		bool(s.support_email),
		"Support email",
		"is empty. Emails offer it for replies and managers receive alerts there.",
		"WARN",
	)
	check(
		bool((s.topup_instructions or "").strip()),
		"Top-up instructions",
		"are empty. Forwarders won't know where to send money.",
	)
	check(
		flt(s.low_balance_threshold) > 0,
		"Low-balance warning level",
		"is 0, so forwarders never get the low-balance email.",
		"WARN",
	)

	account = frappe.get_all("Email Account", {"enable_outgoing": 1, "default_outgoing": 1}, pluck="email_id")
	check(
		bool(account),
		"Default outgoing email account",
		"is missing. No email is sent at all: welcome, password reset, leads, bookings.",
	)

	sys_currency = frappe.db.get_single_value("System Settings", "currency")
	check(
		sys_currency == s.default_currency,
		"Currency",
		f"System Settings says {sys_currency}, Sokan Settings says {s.default_currency}. Make them match.",
		"WARN",
	)
	plan_currencies = set(frappe.get_all("Sokan Plan", {"is_active": 1}, pluck="currency"))
	check(
		plan_currencies <= {s.default_currency},
		"Plan currencies",
		f"plans use {sorted(plan_currencies)}; Sokan Settings uses {s.default_currency}.",
	)
	defaults = frappe.get_all("Sokan Plan", {"is_active": 1, "is_default": 1}, pluck="name")
	check(
		len(defaults) == 1,
		"Default plan",
		f"{len(defaults)} active default plans; there must be exactly one.",
	)

	check(
		not is_scheduler_disabled(),
		"Scheduler",
		"is off. Requests won't expire, plans won't renew, managers get no digest.",
	)
	check(
		not cint(frappe.conf.get("developer_mode")),
		"Developer mode",
		"is on. Turn it off in production (bench --site <site> set-config developer_mode 0).",
		"WARN",
	)
	check(
		bool(frappe.conf.get("host_name", "").startswith("https://")),
		"host_name (site_config)",
		"should be the https backend URL so Frappe builds correct absolute links.",
		"WARN",
	)

	managers = frappe.get_all("Has Role", {"role": ROLE_ADMIN, "parenttype": "User"}, pluck="parent")
	check(bool(managers), "Managers", "none yet. Run: bench --site <site> sokan-add-manager you@example.com")
	desk = frappe.get_all("Role", {"name": ("like", "Sokan%"), "desk_access": 1}, pluck="name")
	check(not desk, "No Desk access for Sokan roles", f"{desk} still open Desk. Run bench migrate.")

	modes = frappe.db.count("Sokan Transport Mode", {"is_active": 1})
	check(modes > 0, "Transport modes", "none active; the request form would be empty.")
	missing = frappe.db.count("Country", {"code": ("in", ("", None))})
	check(
		not missing, "Country codes", f"{missing} countries have no ISO code (flags and names break).", "WARN"
	)

	test = {
		d: frappe.db.count(d)
		for d in ("Freight Request", "Sokan Forwarder", "Sokan Customer", "Sokan Top Up")
	}
	check(
		not any(test.values()),
		"Starting with no test data",
		f"found {test}. Fine on a staging copy; use a fresh site for production.",
		"WARN",
	)
	return out


@click.command("sokan-check")
@pass_context
def go_live_check(context):
	"""Check settings, email, money and access before going live."""
	import frappe

	frappe.init(site=get_site(context))
	frappe.connect()
	try:
		results = run_checks()
	finally:
		frappe.destroy()
	colours = {"OK": "green", "WARN": "yellow", "FAIL": "red"}
	for level, name, detail in results:
		click.secho(f"[{level:4}] ", fg=colours[level], nl=False)
		click.echo(name + (f": {detail}" if detail else ""))
	fails = sum(1 for r in results if r[0] == "FAIL")
	warns = sum(1 for r in results if r[0] == "WARN")
	click.echo(f"\n{fails} to fix, {warns} to review.")
	if fails:
		raise SystemExit(1)


commands = [add_manager, go_live_check]
