"""Who hears about what: one function per business event.

Each sends the matching email from sokan.emails (in every recipient's own
language) and, where useful, a realtime ping for anyone currently online.
Everything here is fire-and-forget: a mail failure is logged, never raised,
so it can't roll back the action that triggered it.

Forwarders control two kinds of email from their profile:
* notify_new_requests  → new lead alerts
* notify_quote_updates → "shipper chose another offer" and new reviews
Bookings, money and account changes are always sent.
"""

import frappe
from frappe.utils import cint, flt, fmt_money, getdate

from sokan import emails
from sokan.utils import ROLE_ADMIN, get_settings

# --------------------------------------------------------------------------- helpers


def _ping(users, event: str, payload: dict):
	for user in users or []:
		frappe.publish_realtime(event, payload, user=user, after_commit=True)


def _forwarder_users(forwarder: str) -> list[str]:
	return frappe.get_all(
		"Sokan Forwarder Member", {"parent": forwarder, "parenttype": "Sokan Forwarder"}, pluck="user"
	)


def _forwarder_recipients(forwarder: str) -> list[str]:
	"""Every team member, or the company email if the team is empty."""
	return _forwarder_users(forwarder) or [frappe.db.get_value("Sokan Forwarder", forwarder, "email")]


def _admins() -> list[str]:
	users = frappe.get_all("Has Role", {"role": ROLE_ADMIN, "parenttype": "User"}, pluck="parent")
	active = frappe.get_all("User", {"name": ("in", users or [""]), "enabled": 1}, pluck="name")
	support = get_settings().support_email
	return list({*active, *([support] if support else [])})


def _money(amount, currency=None) -> str:
	return fmt_money(flt(amount), currency=currency or get_settings().default_currency or "USD")


def _stars(rating) -> str:
	r = max(0, min(5, cint(rating)))
	return "★" * r + "☆" * (5 - r)


def _request(name: str):
	return frappe.db.get_value(
		"Freight Request",
		name,
		[
			"name",
			"title",
			"customer",
			"transport_mode",
			"origin_city",
			"origin_country",
			"destination_city",
			"destination_country",
			"commodity",
			"ready_date",
			"valid_until",
			"quote_count",
		],
		as_dict=True,
	)


def _route(req) -> str:
	a = ", ".join(x for x in (req.origin_city, req.origin_country) if x)
	b = ", ".join(x for x in (req.destination_city, req.destination_country) if x)
	return f"{a} → {b}"


def _customer_user(customer: str | None) -> str | None:
	return frappe.db.get_value("Sokan Customer", customer, "user") if customer else None


def _date(value) -> str | None:
	return getdate(value).strftime("%d %b %Y") if value else None


def _request_facts(req):
	return [
		("request", req.name),
		("route", _route(req)),
		("mode", req.transport_mode),
		("commodity", req.commodity),
		("ready", _date(req.ready_date)),
		("valid_until", _date(req.valid_until)),
	]


# --------------------------------------------------------------------------- accounts


def notify_welcome_shipper(user: str, full_name: str):
	emails.send(
		"welcome_shipper",
		[user],
		{"first_name": (full_name or "").split(" ")[0] or user},
		path="/get-quote",
	)


def notify_welcome_forwarder(forwarder):
	"""Sign-up: 'application received' while pending, the approval email if auto-approved."""
	if forwarder.status == "Active":
		notify_forwarder_status(forwarder)
	else:
		emails.send(
			"welcome_forwarder",
			_forwarder_recipients(forwarder.name),
			{"company": forwarder.company_name},
			path="/partner/profile",
		)


def notify_verification_code(user: str, code: str, minutes: int):
	emails.send("verify_code", [user], {"email": user, "code": code, "minutes": minutes}, now=True)


def notify_password_reset(user: str, key: str, minutes: int):
	emails.send(
		"password_reset",
		[user],
		{"email": user, "minutes": minutes},
		path=f"/reset-password?key={key}",
		now=True,
	)


def notify_password_changed(user: str):
	emails.send("password_changed", [user], {"email": user}, path="/forgot-password", now=True)


def notify_manager_invite(user: str, new_account: bool):
	lang = emails._language(user)
	label = {
		("en", True): "Choose your password",
		("en", False): "Open management",
		("fa", True): "انتخاب رمز عبور",
		("fa", False): "ورود به بخش مدیریت",
	}[(lang, new_account)]
	emails.send(
		"manager_invite",
		[user],
		{
			"email": user,
			"inviter": frappe.utils.get_fullname(frappe.session.user),
			"new_account": new_account,
			"existing_account": not new_account,
			"cta_label": label,
		},
		path=f"/forgot-password?email={user}" if new_account else "/admin",
	)


# --------------------------------------------------------------------------- shippers


def notify_request_published(request_name: str, count: int):
	req = _request(request_name)
	user = _customer_user(req.customer)
	emails.send(
		"request_published",
		[user],
		{"request": req.name, "title": req.title, "count": count, "none": not count},
		facts=_request_facts(req),
		path=f"/account/requests/{req.name}",
	)


def notify_new_quote(quote, is_new: bool = True):
	req = _request(quote.request)
	user = _customer_user(req.customer)
	_ping([user], "sokan:new_quote", {"request": quote.request, "quote": quote.name})
	count = frappe.db.count(
		"Freight Quote", {"request": quote.request, "status": ("in", ("Submitted", "Accepted"))}
	)
	emails.send(
		"new_quote" if is_new else "quote_updated",
		[user],
		{
			"request": req.name,
			"title": req.title,
			"forwarder": quote.forwarder_name,
			"amount": _money(quote.total_amount, quote.currency),
			"count": count,
		},
		facts=lambda lang: [
			("forwarder", quote.forwarder_name),
			("total", _money(quote.total_amount, quote.currency)),
			("transit", emails.days(quote.transit_days_min, quote.transit_days_max, lang)),
			("quote_valid", _date(quote.valid_until)),
		],
		path=f"/account/requests/{quote.request}",
	)


def notify_booking(quote):
	"""Shipper accepted a quote: confirm to the shipper, congratulate the forwarder."""
	req = frappe.get_doc("Freight Request", quote.request)
	fwd = frappe.db.get_value(
		"Sokan Forwarder",
		quote.forwarder,
		["company_name", "email", "phone", "website", "slug"],
		as_dict=True,
	)
	amount = _money(quote.total_amount, quote.currency)

	emails.send(
		"booking_confirmed",
		[_customer_user(req.customer)],
		{"title": req.title, "forwarder": fwd.company_name, "amount": amount},
		facts=[
			("forwarder", fwd.company_name),
			("email", fwd.email),
			("phone", fwd.phone),
			("website", fwd.website),
			("total", amount),
		],
		path=f"/account/requests/{req.name}",
	)

	users = _forwarder_users(quote.forwarder)
	_ping(users, "sokan:quote_accepted", {"quote": quote.name, "request": quote.request})
	emails.send(
		"quote_won",
		users,
		{"title": req.title, "amount": amount},
		facts=[
			("request", req.name),
			("contact", req.contact_name),
			("company", req.contact_company),
			("email", req.contact_email),
			("phone", req.contact_phone),
			("route", _route(req)),
		],
		path=f"/partner/leads/{req.name}",
	)


def notify_request_expired(request_name: str):
	req = _request(request_name)
	count = cint(req.quote_count)
	emails.send(
		"request_expired",
		[_customer_user(req.customer)],
		{"request": req.name, "title": req.title, "count": count, "none": not count},
		path=f"/account/requests/{req.name}" if count else "/get-quote",
	)


def notify_request_cancelled_by_admin(request_name: str, reason: str):
	req = _request(request_name)
	emails.send(
		"request_cancelled_by_admin",
		[_customer_user(req.customer)],
		{"request": req.name, "title": req.title, "reason": reason},
		path="/account/requests",
	)


def notify_review_published(review):
	fwd = frappe.db.get_value(
		"Sokan Forwarder", review.forwarder, ["company_name", "slug", "notify_quote_updates"], as_dict=True
	)
	emails.send(
		"review_published",
		[_customer_user(review.customer)],
		{"forwarder": fwd.company_name},
		path=f"/forwarders/{fwd.slug}",
	)
	if fwd.notify_quote_updates:
		from sokan.api.public import public_name

		emails.send(
			"new_review",
			_forwarder_users(review.forwarder),
			{
				"company": fwd.company_name,
				"rating": review.rating,
				"stars": _stars(review.rating),
				"author": public_name(review.customer_name),
				"comment": review.comment,
			},
			path=f"/forwarders/{fwd.slug}",
		)


# --------------------------------------------------------------------------- forwarders


def notify_new_leads(request_name: str, forwarders: list[str]):
	if not forwarders:
		return
	req = _request(request_name)
	opted_in = set(
		frappe.get_all(
			"Sokan Forwarder", {"name": ("in", forwarders), "notify_new_requests": 1}, pluck="name"
		)
	)
	recipients = []
	for fwd in forwarders:
		users = _forwarder_users(fwd)
		_ping(users, "sokan:new_lead", {"request": request_name, "title": req.title})
		if fwd in opted_in:
			recipients += users
	emails.send(
		"new_lead",
		recipients,
		{"title": req.title},
		facts=_request_facts(req),
		path=f"/partner/leads/{request_name}",
	)


def notify_quote_rejected(quote, reason: str | None = None):
	_ping(_forwarder_users(quote.forwarder), "sokan:quote_rejected", {"quote": quote.name})
	if not frappe.db.get_value("Sokan Forwarder", quote.forwarder, "notify_quote_updates"):
		return
	title = frappe.db.get_value("Freight Request", quote.request, "title")
	emails.send(
		"quote_lost",
		_forwarder_users(quote.forwarder),
		{
			"quote": quote.name,
			"title": title,
			"amount": _money(quote.total_amount, quote.currency),
			"reason": reason,
		},
		path="/partner/leads",
	)


def notify_lead_cancelled(request_name: str, forwarder: str, refund: float | None, currency: str | None):
	title = frappe.db.get_value("Freight Request", request_name, "title")
	emails.send(
		"lead_cancelled",
		_forwarder_users(forwarder),
		{"request": request_name, "title": title, "refund": _money(refund, currency) if refund else None},
		path="/partner/leads",
	)


def notify_forwarder_status(forwarder):
	recipients = _forwarder_recipients(forwarder.name)
	ctx = {"company": forwarder.company_name, "reason": forwarder.rejection_reason or "—"}
	if forwarder.status == "Active":
		bonus = flt(get_settings().signup_bonus)
		already = frappe.db.exists(
			"Sokan Wallet Transaction", {"forwarder": forwarder.name, "transaction_type": "Signup Bonus"}
		)
		ctx["bonus"] = _money(bonus, forwarder.wallet_currency) if bonus and already else None
		ctx["open_leads"] = (
			frappe.db.count("Freight Request Lead", {"forwarder": forwarder.name, "status": "New"}) or None
		)
		emails.send("forwarder_approved", recipients, ctx, path="/partner")
	elif forwarder.status == "Rejected":
		emails.send("forwarder_rejected", recipients, ctx, path="/partner/profile")
	elif forwarder.status == "Suspended":
		emails.send("forwarder_suspended", recipients, ctx, path="/partner")


def notify_topup(topup):
	"""Approved or rejected by a manager."""
	ctx = {"topup": topup.name, "amount": _money(topup.amount, topup.currency), "reason": topup.note or "—"}
	if topup.status == "Approved":
		balance = frappe.db.get_value("Sokan Forwarder", topup.forwarder, "wallet_balance")
		emails.send(
			"topup_approved",
			_forwarder_users(topup.forwarder),
			ctx,
			facts=[("amount", ctx["amount"]), ("balance", _money(balance, topup.currency))],
			path="/partner/wallet",
		)
	else:
		emails.send("topup_rejected", _forwarder_users(topup.forwarder), ctx, path="/partner/wallet")


def notify_topup_requested(topup):
	"""A forwarder asked to top up: acknowledge to them, alert the managers."""
	company = frappe.db.get_value("Sokan Forwarder", topup.forwarder, "company_name")
	amount = _money(topup.amount, topup.currency)
	facts = [
		("company", company),
		("amount", amount),
		("method", topup.payment_method),
		("reference", topup.payment_reference),
	]
	emails.send(
		"topup_received",
		_forwarder_users(topup.forwarder),
		{"topup": topup.name, "amount": amount},
		facts=facts,
		path="/partner/wallet",
	)
	emails.send(
		"admin_new_topup",
		_admins(),
		{"company": company, "amount": amount},
		facts=facts,
		path="/admin/topups",
	)


def notify_low_balance(forwarder: str):
	from sokan.billing import fees_for

	fwd = frappe.get_doc("Sokan Forwarder", forwarder)
	fees = fees_for(fwd)
	emails.send(
		"low_balance",
		_forwarder_users(forwarder),
		{
			"balance": _money(fwd.wallet_balance, fees.currency),
			"threshold": _money(get_settings().low_balance_threshold, fees.currency),
			"view_fee": _money(fees.view_fee, fees.currency),
			"quote_fee": _money(fees.quote_fee, fees.currency),
		},
		path="/partner/wallet",
	)


def notify_wallet_adjusted(forwarder: str, amount: float, note: str):
	cur, balance = frappe.db.get_value("Sokan Forwarder", forwarder, ["wallet_currency", "wallet_balance"])
	signed = ("+" if amount > 0 else "") + _money(amount, cur)
	emails.send(
		"wallet_adjusted",
		_forwarder_users(forwarder),
		{"amount": signed, "note": note},
		facts=[("amount", signed), ("balance", _money(balance, cur))],
		path="/partner/wallet",
	)


def notify_plan_renewed(forwarder: str, plan: str, fee: float, month: str):
	cur, balance = frappe.db.get_value("Sokan Forwarder", forwarder, ["wallet_currency", "wallet_balance"])
	emails.send(
		"plan_renewed",
		_forwarder_users(forwarder),
		{"plan": plan, "fee": _money(fee, cur), "month": month},
		facts=[("plan", plan), ("amount", _money(fee, cur)), ("balance", _money(balance, cur))],
		path="/partner/wallet",
	)


def notify_plan_downgraded(forwarder: str, old_plan: str, new_plan: str, fee: float):
	company, cur = frappe.db.get_value("Sokan Forwarder", forwarder, ["company_name", "wallet_currency"])
	emails.send(
		"plan_downgraded",
		_forwarder_users(forwarder),
		{"plan": new_plan, "old_plan": old_plan, "fee": _money(fee, cur), "company": company},
		path="/partner/wallet",
	)


# --------------------------------------------------------------------------- managers


def notify_admin_new_forwarder(forwarder):
	if forwarder.status != "Pending":
		return
	emails.send(
		"admin_new_forwarder",
		_admins(),
		{"company": forwarder.company_name},
		facts=[
			("company", forwarder.company_name),
			("email", forwarder.email),
			("phone", forwarder.phone),
			("country", forwarder.country),
			("website", forwarder.website),
		],
		path=f"/admin/forwarders/{forwarder.name}",
	)


def notify_admin_new_review(review):
	from sokan.api.public import public_name

	company = frappe.db.get_value("Sokan Forwarder", review.forwarder, "company_name")
	emails.send(
		"admin_new_review",
		_admins(),
		{
			"company": company,
			"rating": review.rating,
			"stars": _stars(review.rating),
			"author": public_name(review.customer_name),
			"comment": review.comment,
		},
		path="/admin/reviews",
	)


def notify_admin_new_message(msg):
	emails.send(
		"admin_new_message",
		_admins(),
		{"name": msg.full_name, "subject_line": msg.subject or msg.full_name, "message": msg.message},
		facts=[("email", msg.email), ("phone", msg.phone), ("company", msg.company)],
		path="/admin/messages",
		reply_to=msg.email,
	)


def send_admin_digest():
	"""Daily: what's waiting, plus yesterday's activity. Skipped when nothing is waiting."""
	from frappe.utils import add_days, nowdate

	from sokan.api.admin import _attention

	att = _attention()
	waiting = {
		"companies": att["forwarders"],
		"topups": att["topups"],
		"reviews": att["reviews"],
		"messages": att["messages"],
	}
	total = sum(waiting.values())
	if not total:
		return
	y = add_days(nowdate(), -1)
	day = {"creation": ("between", (f"{y} 00:00:00", f"{y} 23:59:59"))}
	emails.send(
		"admin_digest",
		_admins(),
		{
			"total": total,
			"requests": frappe.db.count("Freight Request", {**day, "status": ("!=", "Draft")}),
			"quotes": frappe.db.count("Freight Quote", day),
			"bookings": frappe.db.count(
				"Freight Request", {"booked_on": ("between", (f"{y} 00:00:00", f"{y} 23:59:59"))}
			),
		},
		facts=[(k, v) for k, v in waiting.items()],
		path="/admin",
	)
