"""Forwarder (partner) portal endpoints.

Flow for one request:  New lead → unlock (billed) → quote (billed) → accepted / rejected.
"""

import frappe
from frappe import _
from frappe.query_builder.functions import Count
from frappe.utils import add_days, cint, flt, now_datetime, nowdate

from sokan import billing
from sokan.api.serializers import quote_payload, request_full, request_teaser
from sokan.utils import active_forwarder_for_user, forwarder_for_user, get_settings, require_login

PROFILE_FIELDS = (
	"company_name",
	"tagline",
	"about",
	"email",
	"phone",
	"website",
	"country",
	"city",
	"address",
	"established_year",
	"team_size",
	"license_number",
	"certifications",
	"logo",
	"cover_image",
	"notify_new_requests",
	"notify_quote_updates",
	"meta_description",
)


def _forwarder():
	require_login()
	return active_forwarder_for_user()


def _lead(request: str, forwarder: str, *, lock: bool = False):
	name = frappe.db.get_value("Freight Request Lead", {"request": request, "forwarder": forwarder}, "name")
	if not name:
		raise frappe.PermissionError(_("This request was not sent to your company."))
	if lock:
		frappe.db.sql("select name from `tabFreight Request Lead` where name=%s for update", name)
	return frappe.get_doc("Freight Request Lead", name)


# --------------------------------------------------------------------------- dashboard


@frappe.whitelist(methods=["GET"])
def dashboard():
	require_login()
	fwd = frappe.get_doc("Sokan Forwarder", forwarder_for_user())
	status_counts = dict(
		frappe.db.sql(
			"select status, count(*) from `tabFreight Request Lead` where forwarder=%s group by status",
			fwd.name,
		)
	)
	# Leads still worth acting on: request open and not yet quoted by us.
	actionable = frappe.db.sql(
		"""select count(*) from `tabFreight Request Lead` l join `tabFreight Request` r on r.name=l.request
		where l.forwarder=%s and l.status in ('New','Unlocked') and r.status='Open'""",
		fwd.name,
	)[0][0]
	return {
		"company": {
			"name": fwd.name,
			"company_name": fwd.company_name,
			"status": fwd.status,
			"slug": fwd.slug,
			"logo": fwd.logo,
			"is_verified": fwd.is_verified,
			"rejection_reason": fwd.rejection_reason if fwd.status in ("Rejected", "Suspended") else None,
			"profile_complete": _profile_completeness(fwd),
		},
		"wallet": billing.wallet_summary(fwd),
		"stats": {
			"leads_received": fwd.leads_received,
			"leads_unlocked": fwd.leads_unlocked,
			"quotes_sent": fwd.quotes_sent,
			"quotes_won": fwd.quotes_won,
			"win_rate": round(100 * fwd.quotes_won / fwd.quotes_sent) if fwd.quotes_sent else 0,
			"rating": flt(fwd.rating),
			"review_count": fwd.review_count,
			"actionable": actionable,
			"by_status": status_counts,
		},
		"recent": list_leads(page_size=5)["items"] if fwd.status == "Active" else [],
	}


def _profile_completeness(fwd) -> int:
	checks = [
		fwd.logo,
		fwd.tagline,
		fwd.about,
		fwd.phone,
		fwd.website,
		fwd.city,
		fwd.established_year,
		fwd.services,
		fwd.certifications,
	]
	return round(100 * sum(1 for c in checks if c) / len(checks))


# --------------------------------------------------------------------------- leads


@frappe.whitelist(methods=["GET"])
def list_leads(
	status: str | None = None, mode: str | None = None, only_open: int = 1, page: int = 1, page_size: int = 20
):
	fwd = _forwarder()
	page, page_size = max(cint(page), 1), min(max(cint(page_size), 1), 50)
	L = frappe.qb.DocType("Freight Request Lead")
	R = frappe.qb.DocType("Freight Request")
	q = frappe.qb.from_(L).join(R).on(R.name == L.request).where(L.forwarder == fwd.name)
	if status:
		q = q.where(L.status == status)
	if mode:
		q = q.where(R.transport_mode == mode)
	if cint(only_open):
		q = q.where(R.status == "Open")

	total = q.select(Count(L.name)).run()[0][0]
	rows = (
		q.select(L.name, L.request, L.status, L.sent_on, L.seen_on, L.quote)
		.orderby(L.sent_on, order=frappe.qb.desc)
		.limit(page_size)
		.offset((page - 1) * page_size)
		.run(as_dict=True)
	)

	unseen = [r.name for r in rows if not r.seen_on]
	if unseen:
		frappe.db.set_value(
			"Freight Request Lead", {"name": ("in", unseen)}, "seen_on", now_datetime(), update_modified=False
		)

	items = []
	for r in rows:
		item = request_teaser(frappe.get_doc("Freight Request", r.request))
		item["lead"] = {
			"name": r.name,
			"status": r.status,
			"sent_on": r.sent_on,
			"is_new": not r.seen_on,
			"quote": r.quote,
		}
		items.append(item)
	return {"items": items, "total": total, "page": page, "page_size": page_size}


@frappe.whitelist(methods=["GET"])
def get_lead(request: str):
	fwd = _forwarder()
	lead = _lead(request, fwd.name)
	req = frappe.get_doc("Freight Request", request)
	unlocked = lead.status in ("Unlocked", "Quoted") or (lead.status == "Closed" and lead.unlocked_on)
	my_quote = (
		quote_payload(frappe.get_doc("Freight Quote", lead.quote), include_forwarder=False)
		if lead.quote
		else None
	)
	wallet = billing.wallet_summary(fwd)
	return {
		"request": request_full(req) if unlocked else request_teaser(req),
		"lead": {
			"name": lead.name,
			"status": lead.status,
			"unlocked": bool(unlocked),
			"unlocked_on": lead.unlocked_on,
			"unlock_fee": lead.unlock_fee,
			"was_free": lead.was_free,
		},
		"my_quote": my_quote,
		"won": bool(my_quote and my_quote["status"] == "Accepted"),
		"competition": {"quotes": int(req.quote_count or 0), "unlocks": int(req.unlock_count or 0)},
		"pricing": {
			"unlock_fee": 0 if wallet["free_views_left"] else wallet["view_fee"],
			"quote_fee": 0 if wallet["free_quotes_left"] else wallet["quote_fee"],
			"free_views_left": wallet["free_views_left"],
			"free_quotes_left": wallet["free_quotes_left"],
			"balance": wallet["balance"],
			"currency": wallet["currency"],
		},
		"default_currency": req.quote_currency or wallet["currency"],
	}


@frappe.whitelist(methods=["POST"])
def unlock_lead(request: str):
	fwd = _forwarder()
	lead = _lead(request, fwd.name, lock=True)
	if lead.status in ("Unlocked", "Quoted"):
		return get_lead(request)
	if lead.status == "Declined":
		lead.status = "New"
	req_status = frappe.db.get_value("Freight Request", request, "status")
	if req_status != "Open":
		frappe.throw(_("This request is {0} and no longer accepts quotes.").format(_(req_status)))

	charge = billing.charge_unlock(lead)
	lead.db_set(
		{
			"status": "Unlocked",
			"unlocked_on": now_datetime(),
			"unlocked_by": frappe.session.user,
			"unlock_fee": charge.fee,
			"was_free": charge.was_free,
			"wallet_transaction": charge.transaction,
		}
	)
	R = frappe.qb.DocType("Freight Request")
	frappe.qb.update(R).set(R.unlock_count, R.unlock_count + 1).where(R.name == request).run()
	F = frappe.qb.DocType("Sokan Forwarder")
	frappe.qb.update(F).set(F.leads_unlocked, F.leads_unlocked + 1).where(F.name == fwd.name).run()
	return get_lead(request)


@frappe.whitelist(methods=["POST"])
def decline_lead(request: str, reason: str | None = None):
	fwd = _forwarder()
	lead = _lead(request, fwd.name)
	if lead.status == "Quoted":
		frappe.throw(_("Withdraw your quote first."))
	lead.db_set({"status": "Declined", "decline_reason": reason})
	return {"ok": True}


# --------------------------------------------------------------------------- quotes

QUOTE_FIELDS = (
	"currency",
	"transit_days_min",
	"transit_days_max",
	"valid_until",
	"carrier",
	"routing",
	"free_days",
	"service_level",
	"inclusions",
	"exclusions",
	"notes",
)


@frappe.whitelist(methods=["POST"])
def submit_quote(request: str, data: dict | str):
	"""Create or revise this forwarder's quote. Only the first submission is billed."""
	fwd = _forwarder()
	data = frappe.parse_json(data)
	lead = _lead(request, fwd.name, lock=True)
	if lead.status not in ("Unlocked", "Quoted"):
		frappe.throw(_("Unlock the request before quoting."))

	req = frappe.get_doc("Freight Request", request)
	if req.status != "Open":
		frappe.throw(_("This request is {0} and no longer accepts quotes.").format(_(req.status)))

	if lead.quote:
		quote = frappe.get_doc("Freight Quote", lead.quote)
		if quote.status != "Submitted":
			frappe.throw(_("Your quote is {0} and cannot be revised.").format(_(quote.status)))
		quote.set("charges", [])
		is_new = False
	else:
		cap = cint(get_settings().max_quotes_per_request)
		if cap and cint(req.quote_count) >= cap:
			frappe.throw(_("This request already has the maximum number of quotes."))
		quote = frappe.new_doc("Freight Quote")
		quote.update(
			{
				"request": request,
				"forwarder": fwd.name,
				"lead": lead.name,
				"submitted_by": frappe.session.user,
			}
		)
		is_new = True

	for k in QUOTE_FIELDS:
		if k in data:
			quote.set(k, data[k])
	quote.valid_until = quote.valid_until or add_days(nowdate(), 7)
	for c in data.get("charges") or []:
		quote.append(
			"charges",
			{k: c.get(k) for k in ("charge_group", "description", "basis", "quantity", "unit_price")},
		)
	quote.save(ignore_permissions=True)

	if is_new:
		charge = billing.charge_quote(quote)
		quote.db_set(
			{"quote_fee": charge.fee, "was_free": charge.was_free, "wallet_transaction": charge.transaction}
		)
		lead.db_set({"status": "Quoted", "quote": quote.name})
		frappe.db.set_value(
			"Freight Request",
			request,
			"quote_count",
			frappe.db.count("Freight Quote", {"request": request, "status": ("!=", "Withdrawn")}),
			update_modified=False,
		)
		F = frappe.qb.DocType("Sokan Forwarder")
		frappe.qb.update(F).set(F.quotes_sent, F.quotes_sent + 1).where(F.name == fwd.name).run()

	from sokan.notifications import notify_new_quote

	notify_new_quote(quote)
	return get_lead(request)


@frappe.whitelist(methods=["POST"])
def withdraw_quote(request: str):
	fwd = _forwarder()
	lead = _lead(request, fwd.name)
	if not lead.quote:
		frappe.throw(_("You have no quote on this request."))
	quote = frappe.get_doc("Freight Quote", lead.quote)
	if quote.status != "Submitted":
		frappe.throw(_("Your quote is {0}.").format(_(quote.status)))
	quote.db_set("status", "Withdrawn")
	# Fee is not refunded: the customer already saw the price.
	lead.db_set({"status": "Unlocked", "quote": None})
	frappe.db.set_value(
		"Freight Request",
		request,
		"quote_count",
		frappe.db.count("Freight Quote", {"request": request, "status": ("!=", "Withdrawn")}),
		update_modified=False,
	)
	return get_lead(request)


@frappe.whitelist(methods=["GET"])
def list_quotes(status: str | None = None, page: int = 1, page_size: int = 20):
	fwd = _forwarder()
	filters = {"forwarder": fwd.name}
	if status:
		filters["status"] = status
	page, page_size = max(cint(page), 1), min(max(cint(page_size), 1), 50)
	names = frappe.get_all(
		"Freight Quote",
		filters,
		pluck="name",
		order_by="creation desc",
		limit=page_size,
		start=(page - 1) * page_size,
	)
	items = []
	for n in names:
		q = frappe.get_doc("Freight Quote", n)
		row = quote_payload(q, include_forwarder=False)
		row["request_title"] = frappe.db.get_value("Freight Request", q.request, "title")
		items.append(row)
	return {"items": items, "total": frappe.db.count("Freight Quote", filters)}


# --------------------------------------------------------------------------- wallet


@frappe.whitelist(methods=["GET"])
def wallet(page: int = 1, page_size: int = 25):
	require_login()
	fwd = frappe.get_doc("Sokan Forwarder", forwarder_for_user())
	page, page_size = max(cint(page), 1), min(max(cint(page_size), 1), 100)
	filters = {"forwarder": fwd.name}
	return {
		"summary": billing.wallet_summary(fwd),
		"transactions": frappe.get_all(
			"Sokan Wallet Transaction",
			filters,
			[
				"name",
				"transaction_type",
				"amount",
				"balance_after",
				"currency",
				"posting_date",
				"description",
				"reference_doctype",
				"reference_name",
			],
			order_by="creation desc",
			limit=page_size,
			start=(page - 1) * page_size,
		),
		"total": frappe.db.count("Sokan Wallet Transaction", filters),
		"topups": frappe.get_all(
			"Sokan Top Up",
			filters,
			[
				"name",
				"amount",
				"currency",
				"payment_method",
				"payment_reference",
				"status",
				"creation",
				"note",
			],
			order_by="creation desc",
			limit=10,
		),
		"instructions": get_settings().topup_instructions,
	}


@frappe.whitelist(methods=["POST"])
def request_topup(
	amount: float,
	payment_method: str = "Bank Transfer",
	payment_reference: str | None = None,
	receipt: str | None = None,
):
	require_login()
	fwd = forwarder_for_user()
	if flt(amount) <= 0:
		frappe.throw(_("Enter an amount greater than zero."))
	if frappe.db.count("Sokan Top Up", {"forwarder": fwd, "status": "Pending"}) >= 3:
		frappe.throw(_("You already have pending top-ups. Please wait for them to be reviewed."))
	doc = frappe.get_doc(
		{
			"doctype": "Sokan Top Up",
			"forwarder": fwd,
			"amount": flt(amount, 2),
			"payment_method": payment_method
			if payment_method in ("Bank Transfer", "Card", "Online Gateway", "Cash")
			else "Bank Transfer",
			"payment_reference": payment_reference,
			"receipt": receipt,
		}
	).insert(ignore_permissions=True)
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist(methods=["POST"])
def change_plan(plan: str):
	fwd = _forwarder()
	if not frappe.db.get_value("Sokan Plan", {"name": plan, "is_active": 1}):
		frappe.throw(_("Unknown plan."))
	if plan == fwd.plan:
		return billing.wallet_summary(fwd)
	fee = flt(frappe.db.get_value("Sokan Plan", plan, "monthly_fee"))
	if fee > 0:
		# Upgrades start immediately and are billed for the first month up front.
		billing.post(fwd.name, "Subscription", -fee, description=_("{0} plan — first month").format(plan))
	frappe.db.set_value(
		"Sokan Forwarder",
		fwd.name,
		{"plan": plan, "plan_renews_on": add_days(nowdate(), 30) if fee > 0 else None},
	)
	return billing.wallet_summary(frappe.get_doc("Sokan Forwarder", fwd.name))


# --------------------------------------------------------------------------- profile


@frappe.whitelist(methods=["GET"])
def get_profile():
	require_login()
	fwd = frappe.get_doc("Sokan Forwarder", forwarder_for_user())
	data = {k: fwd.get(k) for k in PROFILE_FIELDS}
	data.update(
		{
			"name": fwd.name,
			"slug": fwd.slug,
			"status": fwd.status,
			"is_verified": fwd.is_verified,
			"modes": [s.transport_mode for s in fwd.services],
			"coverage": [c.country for c in fwd.coverage],
			"members": [
				{"user": m.user, "full_name": m.full_name, "role": m.member_role} for m in fwd.members
			],
		}
	)
	return data


@frappe.whitelist(methods=["POST"])
def update_profile(data: dict | str):
	require_login()
	data = frappe.parse_json(data)
	fwd = frappe.get_doc("Sokan Forwarder", forwarder_for_user())
	role = next((m.member_role for m in fwd.members if m.user == frappe.session.user), None)
	if role not in ("Owner", "Manager"):
		frappe.throw(_("Only owners and managers can edit the company profile."), frappe.PermissionError)
	for k in PROFILE_FIELDS:
		if k in data:
			fwd.set(k, data[k])
	if "modes" in data:
		fwd.set("services", [{"transport_mode": m} for m in data["modes"]])
	if "coverage" in data:
		fwd.set("coverage", [{"country": c} for c in data["coverage"]])
	fwd.save(ignore_permissions=True)
	return get_profile()
