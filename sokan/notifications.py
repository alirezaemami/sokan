"""Outbound messages: queued email plus a realtime ping for anyone online.

Every function here is fire-and-forget — a mail failure must never roll back
the business transaction that triggered it.
"""

import frappe
from frappe import _
from frappe.utils import escape_html

from sokan.utils import ROLE_ADMIN, frontend_url, get_settings


def _layout(heading: str, body: str, cta: tuple[str, str] | None = None) -> str:
	button = (
		f'<p style="margin:28px 0"><a href="{cta[1]}" style="background:#4f46e5;color:#fff;'
		f'padding:12px 22px;border-radius:10px;text-decoration:none;font-weight:600">{escape_html(cta[0])}</a></p>'
		if cta
		else ""
	)
	name = escape_html(get_settings().platform_name or "Sokan")
	return (
		'<div style="font-family:Inter,Segoe UI,Arial,sans-serif;max-width:560px;margin:auto;color:#0f172a">'
		f'<p style="font-size:20px;font-weight:800;letter-spacing:-.02em;color:#4f46e5">{name}</p>'
		f'<h2 style="font-size:22px;margin:8px 0 12px">{escape_html(heading)}</h2>'
		f'<div style="font-size:15px;line-height:1.6;color:#334155">{body}</div>{button}'
		f'<p style="font-size:12px;color:#94a3b8;margin-top:32px">{name} · {frontend_url()}</p></div>'
	)


def _send(recipients, subject: str, heading: str, body: str, cta=None):
	recipients = [r for r in (recipients or []) if r and r not in ("Administrator", "Guest")]
	if not recipients:
		return
	try:
		frappe.sendmail(
			recipients=recipients, subject=subject, message=_layout(heading, body, cta), delayed=True
		)
	except Exception:
		frappe.log_error(title="Sokan email failed")


def _ping(users, event: str, payload: dict):
	for user in users or []:
		frappe.publish_realtime(event, payload, user=user, after_commit=True)


def _forwarder_users(forwarder: str) -> list[str]:
	return frappe.get_all(
		"Sokan Forwarder Member", {"parent": forwarder, "parenttype": "Sokan Forwarder"}, pluck="user"
	)


def _admins() -> list[str]:
	users = frappe.get_all("Has Role", {"role": ROLE_ADMIN, "parenttype": "User"}, pluck="parent")
	support = get_settings().support_email
	return list({*users, *([support] if support else [])})


# --------------------------------------------------------------------------- forwarders


def notify_new_leads(request_name: str, forwarders: list[str]):
	if not forwarders:
		return
	req = frappe.db.get_value(
		"Freight Request", request_name, ["title", "commodity", "ready_date"], as_dict=True
	)
	url = frontend_url(f"/partner/leads/{request_name}")
	opted_in = set(
		frappe.get_all(
			"Sokan Forwarder", {"name": ("in", forwarders), "notify_new_requests": 1}, pluck="name"
		)
	)
	for fwd in forwarders:
		users = _forwarder_users(fwd)
		_ping(users, "sokan:new_lead", {"request": request_name, "title": req.title})
		if fwd in opted_in:
			_send(
				users,
				_("New freight request: {0}").format(req.title),
				_("A new shipment needs a price"),
				_("<b>{0}</b><br>Commodity: {1}<br>Cargo ready: {2}").format(
					escape_html(req.title), escape_html(req.commodity or ""), req.ready_date
				),
				(_("View request"), url),
			)


def notify_quote_accepted(quote):
	users = _forwarder_users(quote.forwarder)
	_ping(users, "sokan:quote_accepted", {"quote": quote.name, "request": quote.request})
	if frappe.db.get_value("Sokan Forwarder", quote.forwarder, "notify_quote_updates"):
		_send(
			users,
			_("Your quote {0} was accepted").format(quote.name),
			_("You won the shipment"),
			_(
				"The customer accepted your quote for request {0}. Their contact details are in the portal — reach out to confirm the booking."
			).format(quote.request),
			(_("Open booking"), frontend_url(f"/partner/leads/{quote.request}")),
		)


def notify_quote_rejected(quote):
	_ping(_forwarder_users(quote.forwarder), "sokan:quote_rejected", {"quote": quote.name})


def notify_forwarder_status(forwarder):
	messages = {
		"Active": (
			_("Your company is live on Sokan"),
			_("You can now receive freight requests and send quotes."),
		),
		"Rejected": (_("Your Sokan application"), _("We could not approve your company. Reason: {0}")),
		"Suspended": (_("Your Sokan account is suspended"), _("Reason: {0}")),
	}
	heading, body = messages[forwarder.status]
	_send(
		_forwarder_users(forwarder.name) or [forwarder.email],
		heading,
		heading,
		body.format(escape_html(forwarder.rejection_reason or "—")),
		(_("Go to partner portal"), frontend_url("/partner")),
	)


def notify_topup(topup):
	approved = topup.status == "Approved"
	_send(
		_forwarder_users(topup.forwarder),
		_("Top-up {0} {1}").format(topup.name, _(topup.status).lower()),
		_("Wallet top-up approved") if approved else _("Wallet top-up rejected"),
		_("Amount: {0} {1}").format(topup.amount, topup.currency)
		+ (f"<br>{escape_html(topup.note)}" if topup.note else ""),
		(_("Open wallet"), frontend_url("/partner/wallet")),
	)


# --------------------------------------------------------------------------- customers


def notify_new_quote(quote):
	req = frappe.db.get_value(
		"Freight Request", quote.request, ["title", "owner", "contact_email"], as_dict=True
	)
	user = frappe.db.get_value(
		"Sokan Customer", frappe.db.get_value("Freight Request", quote.request, "customer"), "user"
	)
	_ping([user], "sokan:new_quote", {"request": quote.request, "quote": quote.name})
	_send(
		[user],
		_("New quote for {0}").format(req.title),
		_("You have a new price"),
		_("{0} quoted <b>{1} {2}</b> for {3}.").format(
			escape_html(quote.forwarder_name),
			frappe.utils.fmt_money(quote.total_amount),
			quote.currency,
			escape_html(req.title),
		),
		(_("Compare quotes"), frontend_url(f"/account/requests/{quote.request}")),
	)


# --------------------------------------------------------------------------- admins


def notify_admin_new_forwarder(forwarder):
	if forwarder.status != "Pending":
		return
	_send(
		_admins(),
		_("New forwarder awaiting approval: {0}").format(forwarder.company_name),
		_("A forwarder signed up"),
		_("{0} ({1}) registered and is waiting for approval.").format(
			escape_html(forwarder.company_name), escape_html(forwarder.email)
		),
		(_("Review in Desk"), frappe.utils.get_url(f"/app/sokan-forwarder/{forwarder.name}")),
	)
