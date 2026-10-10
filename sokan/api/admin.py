"""Manager API behind the Nuxt admin portal (/admin).

Managers never use Desk. Everything they do goes through this module, so
the rules are kept deliberately plain:

* every endpoint calls ``_require_admin()`` first — Sokan Admin or System
  Manager, nobody else;
* reads are GET, writes are POST (Frappe enforces the CSRF token on POST);
* writes only touch fields named in an explicit allowlist, and money moves
  only through the wallet ledger (``sokan.billing.post``), never by setting
  a balance.
"""

import frappe
from frappe import _
from frappe.utils import (
	add_days,
	add_months,
	cint,
	flt,
	get_first_day,
	getdate,
	now_datetime,
	nowdate,
	strip_html,
)

from sokan import billing
from sokan.api.serializers import quote_payload, request_full
from sokan.utils import ROLE_ADMIN, add_role, platform_currency
from sokan.verification import FIELD as VERIFIED_FIELD
from sokan.verification import mark_verified

# Ledger types that are platform income (charged to forwarders).
REVENUE_TYPES = ("Request Unlock", "Quote Fee", "Subscription")
MAX_PAGE_SIZE = 100


# ---------------------------------------------------------------- helpers


def _require_admin():
	if frappe.session.user == "Guest":
		frappe.throw(_("Please sign in to continue."), frappe.AuthenticationError)
	if not {ROLE_ADMIN, "System Manager"} & set(frappe.get_roles()):
		frappe.throw(_("This area is for Sokan managers only."), frappe.PermissionError)


def _paging(page, page_size, default: int = 20) -> tuple[int, int]:
	page = max(cint(page), 1)
	size = min(max(cint(page_size) or default, 1), MAX_PAGE_SIZE)
	return (page - 1) * size, size


def _like(text: str | None) -> str | None:
	text = (text or "").strip()
	return f"%{text}%" if text else None


def _clean(data, allowed: dict[str, type]) -> dict:
	"""Keep only allowlisted keys, coerced to their type."""
	data = frappe.parse_json(data) or {}
	out = {}
	for key, kind in allowed.items():
		if key not in data:
			continue
		value = data[key]
		if kind is bool:
			out[key] = 1 if cint(value) else 0
		elif kind is int:
			out[key] = cint(value)
		elif kind is float:
			out[key] = flt(value)
		else:
			out[key] = (str(value).strip() if value is not None else None) or None
	return out


def _date_range(from_date=None, to_date=None, default_days: int = 30):
	end = getdate(to_date) if to_date else getdate(nowdate())
	start = getdate(from_date) if from_date else add_days(end, -(default_days - 1))
	if start > end:
		start, end = end, start
	return start, end


def _revenue(start=None, end=None) -> float:
	cond, args = "", {"types": REVENUE_TYPES}
	if start:
		cond += " and date(posting_date) >= %(start)s"
		args["start"] = start
	if end:
		cond += " and date(posting_date) <= %(end)s"
		args["end"] = end
	return flt(
		frappe.db.sql(
			f"select -sum(amount) from `tabSokan Wallet Transaction` where transaction_type in %(types)s{cond}",
			args,
		)[0][0]
	)


def _daily(sql: str, start, end, args: dict | None = None) -> dict[str, float]:
	rows = frappe.db.sql(sql, {"start": start, "end": end, **(args or {})})
	return {str(d): flt(v) for d, v in rows}


# ---------------------------------------------------------------- overview


def _verified_map(emails) -> dict[str, bool]:
	"""Whether each address has been confirmed with a code (Desk users always count)."""
	emails = [e for e in set(emails) if e]
	if not emails:
		return {}
	rows = frappe.get_all(
		"User", filters={"name": ("in", emails)}, fields=["name", "user_type", VERIFIED_FIELD]
	)
	return {r.name: bool(r.get(VERIFIED_FIELD)) or r.user_type == "System User" for r in rows}


def _awaiting_email() -> list[str]:
	"""Pending forwarders whose owner hasn't confirmed their email yet: not ready for review."""
	return frappe.db.sql_list(
		f"""select f.name from `tabSokan Forwarder` f join `tabUser` u on u.name = f.email
		where f.status = 'Pending' and u.user_type = 'Website User' and ifnull(u.{VERIFIED_FIELD}, 0) = 0"""
	)


def _attention() -> dict:
	return {
		"forwarders": frappe.db.count("Sokan Forwarder", {"status": "Pending"}) - len(_awaiting_email()),
		"topups": frappe.db.count("Sokan Top Up", {"status": "Pending"}),
		"reviews": frappe.db.count("Sokan Review", {"status": "Pending"}),
		"messages": frappe.db.count("Sokan Contact Message", {"status": "New"}),
	}


@frappe.whitelist(methods=["GET"])
def attention():
	"""Work waiting for a manager; drives the badges in the admin navigation."""
	_require_admin()
	return _attention()


@frappe.whitelist(methods=["GET"])
def overview():
	_require_admin()
	today = getdate(nowdate())
	month_start = get_first_day(today)
	last_month_start = add_months(month_start, -1)
	start = add_days(today, -29)

	forwarders = dict(frappe.db.sql("select status, count(*) from `tabSokan Forwarder` group by status"))
	requests = dict(frappe.db.sql("select status, count(*) from `tabFreight Request` group by status"))

	requests_daily = _daily(
		"""select date(published_on), count(*) from `tabFreight Request`
		where published_on is not null and date(published_on) between %(start)s and %(end)s group by 1""",
		start,
		today,
	)
	quotes_daily = _daily(
		"""select date(creation), count(*) from `tabFreight Quote`
		where date(creation) between %(start)s and %(end)s group by 1""",
		start,
		today,
	)
	revenue_daily = _daily(
		"""select date(posting_date), -sum(amount) from `tabSokan Wallet Transaction`
		where transaction_type in %(types)s and date(posting_date) between %(start)s and %(end)s group by 1""",
		start,
		today,
		{"types": REVENUE_TYPES},
	)
	days = [str(add_days(start, i)) for i in range(30)]

	pending_topups = frappe.db.sql(
		"select coalesce(sum(amount), 0) from `tabSokan Top Up` where status='Pending'"
	)[0]

	return {
		"currency": platform_currency(),
		"kpis": {
			"forwarders_active": forwarders.get("Active", 0),
			"forwarders_total": sum(forwarders.values()),
			"customers": frappe.db.count("Sokan Customer"),
			"requests_open": requests.get("Open", 0),
			"requests_booked": requests.get("Booked", 0),
			"requests_total": sum(v for k, v in requests.items() if k != "Draft"),
			"quotes": frappe.db.count("Freight Quote"),
			"revenue_month": _revenue(month_start, today),
			"revenue_last_month": _revenue(last_month_start, add_days(month_start, -1)),
			"revenue_total": _revenue(),
			"wallet_float": flt(frappe.db.sql("select sum(wallet_balance) from `tabSokan Forwarder`")[0][0]),
		},
		"attention": {**_attention(), "topups_amount": flt(pending_topups[0])},
		"series": [
			{
				"date": d,
				"requests": requests_daily.get(d, 0),
				"quotes": quotes_daily.get(d, 0),
				"revenue": revenue_daily.get(d, 0),
			}
			for d in days
		],
		"recent_requests": frappe.get_all(
			"Freight Request",
			filters={"status": ("!=", "Draft")},
			fields=[
				"name",
				"title",
				"status",
				"customer_name",
				"transport_mode",
				"leads_sent",
				"quote_count",
				"creation",
			],
			order_by="creation desc",
			limit=6,
		),
		"pending_forwarders": frappe.get_all(
			"Sokan Forwarder",
			filters={"status": "Pending", "name": ("not in", _awaiting_email() or [""])},
			fields=["name", "company_name", "country", "city", "logo", "creation"],
			order_by="creation asc",
			limit=5,
		),
	}


# ---------------------------------------------------------------- reports


@frappe.whitelist(methods=["GET"])
def reports(from_date: str | None = None, to_date: str | None = None):
	_require_admin()
	start, end = _date_range(from_date, to_date, default_days=90)
	args = {"start": start, "end": end}

	def one(sql: str, extra: dict | None = None):
		return frappe.db.sql(sql, {**args, **(extra or {})})[0][0] or 0

	published = one(
		"select count(*) from `tabFreight Request` where published_on is not null and date(published_on) between %(start)s and %(end)s"
	)
	leads = one(
		"select count(*) from `tabFreight Request Lead` where date(sent_on) between %(start)s and %(end)s"
	)
	unlocks = one(
		"select count(*) from `tabFreight Request Lead` where unlocked_on is not null and date(unlocked_on) between %(start)s and %(end)s"
	)
	quotes = one("select count(*) from `tabFreight Quote` where date(creation) between %(start)s and %(end)s")
	booked = one(
		"select count(*) from `tabFreight Request` where booked_on is not null and date(booked_on) between %(start)s and %(end)s"
	)

	by_type = dict(
		frappe.db.sql(
			"""select transaction_type, sum(amount) from `tabSokan Wallet Transaction`
			where date(posting_date) between %(start)s and %(end)s group by transaction_type""",
			args,
		)
	)

	# Twelve calendar months ending with the month of `end`.
	first = add_months(get_first_day(end), -11)
	monthly_args = {"first": first, "end": end, "types": REVENUE_TYPES}

	def by_month(sql: str) -> dict[str, float]:
		return {k: flt(v) for k, v in frappe.db.sql(sql, monthly_args)}

	m_revenue = by_month(
		"""select date_format(posting_date, '%%Y-%%m'), -sum(amount) from `tabSokan Wallet Transaction`
		where transaction_type in %(types)s and date(posting_date) between %(first)s and %(end)s group by 1"""
	)
	m_topups = by_month(
		"""select date_format(posting_date, '%%Y-%%m'), sum(amount) from `tabSokan Wallet Transaction`
		where transaction_type='Top-up' and date(posting_date) between %(first)s and %(end)s group by 1"""
	)
	m_requests = by_month(
		"""select date_format(published_on, '%%Y-%%m'), count(*) from `tabFreight Request`
		where published_on is not null and date(published_on) between %(first)s and %(end)s group by 1"""
	)
	m_booked = by_month(
		"""select date_format(booked_on, '%%Y-%%m'), count(*) from `tabFreight Request`
		where booked_on is not null and date(booked_on) between %(first)s and %(end)s group by 1"""
	)
	months = [str(add_months(first, i))[:7] for i in range(12)]

	lanes = frappe.db.sql(
		"""select origin_country, destination_country, count(*) as requests, sum(status='Booked') as booked
		from `tabFreight Request` where published_on is not null and date(published_on) between %(start)s and %(end)s
		group by origin_country, destination_country order by requests desc limit 10""",
		args,
		as_dict=True,
	)
	modes = frappe.db.sql(
		"""select transport_mode as mode, count(*) as requests, sum(status='Booked') as booked
		from `tabFreight Request` where published_on is not null and date(published_on) between %(start)s and %(end)s
		group by transport_mode order by requests desc""",
		args,
		as_dict=True,
	)
	top_forwarders = frappe.db.sql(
		"""select f.name, f.company_name, f.country,
			(select count(*) from `tabFreight Quote` q where q.forwarder=f.name and date(q.creation) between %(start)s and %(end)s) as quotes,
			(select count(*) from `tabFreight Quote` q where q.forwarder=f.name and q.status='Accepted'
				and date(q.accepted_on) between %(start)s and %(end)s) as won,
			(select count(*) from `tabFreight Request Lead` l where l.forwarder=f.name and l.unlocked_on is not null
				and date(l.unlocked_on) between %(start)s and %(end)s) as unlocks,
			(select coalesce(-sum(t.amount), 0) from `tabSokan Wallet Transaction` t where t.forwarder=f.name
				and t.transaction_type in %(types)s and date(t.posting_date) between %(start)s and %(end)s) as fees
		from `tabSokan Forwarder` f where f.status='Active'
		order by fees desc, quotes desc limit 10""",
		{**args, "types": REVENUE_TYPES},
		as_dict=True,
	)

	return {
		"from_date": str(start),
		"to_date": str(end),
		"currency": platform_currency(),
		"funnel": {
			"published": published,
			"leads": leads,
			"unlocks": unlocks,
			"quotes": quotes,
			"booked": booked,
		},
		"revenue": {
			"unlocks": -flt(by_type.get("Request Unlock")),
			"quotes": -flt(by_type.get("Quote Fee")),
			"subscriptions": -flt(by_type.get("Subscription")),
			"topups": flt(by_type.get("Top-up")),
			"bonuses": flt(by_type.get("Signup Bonus")),
			"refunds": flt(by_type.get("Refund")),
			"adjustments": flt(by_type.get("Adjustment")),
		},
		"averages": {
			"leads_per_request": flt(leads / published, 1) if published else 0,
			"quotes_per_request": flt(quotes / published, 1) if published else 0,
			"booking_rate": flt(100 * booked / published, 1) if published else 0,
		},
		"monthly": [
			{
				"month": m,
				"revenue": m_revenue.get(m, 0),
				"topups": m_topups.get(m, 0),
				"requests": m_requests.get(m, 0),
				"booked": m_booked.get(m, 0),
			}
			for m in months
		],
		"lanes": lanes,
		"modes": modes,
		"top_forwarders": top_forwarders,
	}


# ---------------------------------------------------------------- forwarders

FORWARDER_LIST_FIELDS = [
	"name",
	"company_name",
	"slug",
	"logo",
	"status",
	"is_verified",
	"is_featured",
	"country",
	"city",
	"email",
	"plan",
	"wallet_balance",
	"wallet_currency",
	"leads_received",
	"quotes_sent",
	"quotes_won",
	"rating",
	"review_count",
	"creation",
]

FORWARDER_EDITABLE = {
	"company_name": str,
	"tagline": str,
	"email": str,
	"phone": str,
	"website": str,
	"country": str,
	"city": str,
	"plan": str,
	"is_verified": bool,
	"is_featured": bool,
}


@frappe.whitelist(methods=["GET"])
def list_forwarders(search: str | None = None, status: str | None = None, page: int = 1, page_size: int = 20):
	_require_admin()
	start, size = _paging(page, page_size)
	filters = {"status": status} if status else {}
	or_filters = None
	if like := _like(search):
		or_filters = {
			"company_name": ("like", like),
			"email": ("like", like),
			"city": ("like", like),
			"name": ("like", like),
		}
	items = frappe.get_all(
		"Sokan Forwarder",
		filters=filters,
		or_filters=or_filters,
		fields=FORWARDER_LIST_FIELDS,
		order_by="creation desc",
		start=start,
		page_length=size,
	)
	total = len(frappe.get_all("Sokan Forwarder", filters=filters, or_filters=or_filters, pluck="name"))
	counts = dict(frappe.db.sql("select status, count(*) from `tabSokan Forwarder` group by status"))
	verified = _verified_map(i.email for i in items)
	for i in items:
		i.email_verified = verified.get(i.email, True)
	return {"items": items, "total": total, "counts": counts}


@frappe.whitelist(methods=["GET"])
def get_forwarder(name: str):
	_require_admin()
	doc = frappe.get_doc("Sokan Forwarder", name)
	data = {f: doc.get(f) for f in FORWARDER_LIST_FIELDS}
	data.update(
		{
			"tagline": doc.tagline,
			"about": strip_html(doc.about or ""),
			"phone": doc.phone,
			"website": doc.website,
			"address": doc.address,
			"established_year": doc.established_year,
			"team_size": doc.team_size,
			"license_number": doc.license_number,
			"license_document": doc.license_document,
			"certifications": doc.certifications,
			"rejection_reason": doc.rejection_reason,
			"leads_unlocked": doc.leads_unlocked,
			"email_verified": _verified_map([doc.email]).get(doc.email, True),
			"services": [s.transport_mode for s in doc.services],
			"coverage": [c.country for c in doc.coverage],
			"members": [
				{
					"user": m.user,
					"full_name": m.full_name,
					"member_role": m.member_role,
					"enabled": frappe.db.get_value("User", m.user, "enabled"),
					"last_login": frappe.db.get_value("User", m.user, "last_login"),
				}
				for m in doc.members
			],
			"wallet": billing.wallet_summary(doc),
			"transactions": frappe.get_all(
				"Sokan Wallet Transaction",
				filters={"forwarder": name},
				fields=[
					"name",
					"transaction_type",
					"amount",
					"balance_after",
					"currency",
					"posting_date",
					"description",
				],
				order_by="posting_date desc",
				limit=15,
			),
			"topups": frappe.get_all(
				"Sokan Top Up",
				filters={"forwarder": name},
				fields=["name", "amount", "currency", "status", "payment_method", "creation"],
				order_by="creation desc",
				limit=10,
			),
			"lead_counts": dict(
				frappe.db.sql(
					"select status, count(*) from `tabFreight Request Lead` where forwarder=%s group by status",
					name,
				)
			),
			"quotes": frappe.get_all(
				"Freight Quote",
				filters={"forwarder": name},
				fields=["name", "request", "status", "total_amount", "currency", "creation"],
				order_by="creation desc",
				limit=10,
			),
		}
	)
	return data


@frappe.whitelist(methods=["POST"])
def set_forwarder_status(name: str, status: str, reason: str | None = None):
	_require_admin()
	if status not in ("Pending", "Active", "Suspended", "Rejected"):
		frappe.throw(_("Unknown status."))
	if status in ("Suspended", "Rejected") and not (reason or "").strip():
		frappe.throw(_("Please give a reason. The company will see it."))
	doc = frappe.get_doc("Sokan Forwarder", name)
	doc.status = status
	doc.rejection_reason = reason.strip() if status in ("Suspended", "Rejected") else None
	# Saving runs the controller: welcome credit, notification and lead backfill.
	doc.save(ignore_permissions=True)
	return get_forwarder(name)


@frappe.whitelist(methods=["POST"])
def update_forwarder(name: str, data: dict | str):
	_require_admin()
	values = _clean(data, FORWARDER_EDITABLE)
	if "company_name" in values and not values["company_name"]:
		frappe.throw(_("Company name is required."))
	if values.get("plan") and not frappe.db.exists("Sokan Plan", values["plan"]):
		frappe.throw(_("Unknown plan."))
	doc = frappe.get_doc("Sokan Forwarder", name)
	doc.update(values)
	doc.save(ignore_permissions=True)
	return get_forwarder(name)


@frappe.whitelist(methods=["POST"])
def adjust_wallet(name: str, amount: float, note: str):
	"""Credit (positive) or debit (negative) a wallet through the ledger."""
	_require_admin()
	amount = flt(amount, 2)
	note = (note or "").strip()
	if not amount:
		frappe.throw(_("Enter a non-zero amount."))
	if abs(amount) > 1_000_000:
		frappe.throw(_("That amount is too large for a manual adjustment."))
	if not note:
		frappe.throw(_("Please add a note explaining the adjustment."))
	billing.post(
		name,
		"Adjustment",
		amount,
		description=_("{0} (by {1})").format(note, frappe.utils.get_fullname(frappe.session.user)),
	)
	from sokan.notifications import notify_wallet_adjusted

	notify_wallet_adjusted(name, amount, note)
	return get_forwarder(name)


# ---------------------------------------------------------------- customers


@frappe.whitelist(methods=["GET"])
def list_customers(search: str | None = None, blocked: int | None = None, page: int = 1, page_size: int = 20):
	_require_admin()
	start, size = _paging(page, page_size)
	filters = {}
	if blocked not in (None, ""):
		filters["is_blocked"] = cint(blocked)
	or_filters = None
	if like := _like(search):
		or_filters = {
			"full_name": ("like", like),
			"email": ("like", like),
			"company_name": ("like", like),
			"name": ("like", like),
		}
	items = frappe.get_all(
		"Sokan Customer",
		filters=filters,
		or_filters=or_filters,
		fields=[
			"name",
			"user",
			"full_name",
			"email",
			"phone",
			"customer_type",
			"company_name",
			"country",
			"city",
			"requests_count",
			"bookings_count",
			"is_blocked",
			"creation",
		],
		order_by="creation desc",
		start=start,
		page_length=size,
	)
	total = len(frappe.get_all("Sokan Customer", filters=filters, or_filters=or_filters, pluck="name"))
	verified = _verified_map(i.user for i in items)
	for i in items:
		i.email_verified = verified.get(i.user, True)
	return {"items": items, "total": total}


@frappe.whitelist(methods=["GET"])
def get_customer(name: str):
	_require_admin()
	doc = frappe.get_doc("Sokan Customer", name)
	data = doc.as_dict(no_default_fields=True, no_child_table_fields=True)
	data["name"] = doc.name
	data["creation"] = doc.creation
	data["last_login"] = frappe.db.get_value("User", doc.user, "last_login") if doc.user else None
	data["email_verified"] = _verified_map([doc.user]).get(doc.user, True)
	data["requests"] = frappe.get_all(
		"Freight Request",
		filters={"customer": name},
		fields=["name", "title", "status", "quote_count", "creation"],
		order_by="creation desc",
		limit=20,
	)
	return data


@frappe.whitelist(methods=["POST"])
def mark_email_verified(user: str):
	"""A manager vouches for an address (e.g. the person confirmed it by phone).
	Does what confirming the code does: welcome email, review queue or auto-approval."""
	_require_admin()
	if frappe.db.get_value("User", user, "user_type") != "Website User":
		frappe.throw(_("Only website accounts need email confirmation."))
	mark_verified(user)
	return {"user": user, "email_verified": True}


@frappe.whitelist(methods=["POST"])
def set_customer_blocked(name: str, blocked: int):
	_require_admin()
	frappe.db.set_value("Sokan Customer", name, "is_blocked", 1 if cint(blocked) else 0)
	return get_customer(name)


# ---------------------------------------------------------------- requests


@frappe.whitelist(methods=["GET"])
def list_requests(
	search: str | None = None,
	status: str | None = None,
	mode: str | None = None,
	customer: str | None = None,
	page: int = 1,
	page_size: int = 20,
):
	_require_admin()
	start, size = _paging(page, page_size)
	filters = {}
	if status:
		filters["status"] = status
	if mode:
		filters["transport_mode"] = mode
	if customer:
		filters["customer"] = customer
	or_filters = None
	if like := _like(search):
		or_filters = {
			"name": ("like", like),
			"title": ("like", like),
			"customer_name": ("like", like),
			"commodity": ("like", like),
		}
	items = frappe.get_all(
		"Freight Request",
		filters=filters,
		or_filters=or_filters,
		fields=[
			"name",
			"title",
			"status",
			"customer",
			"customer_name",
			"transport_mode",
			"origin_country",
			"destination_country",
			"leads_sent",
			"unlock_count",
			"quote_count",
			"valid_until",
			"published_on",
			"creation",
		],
		order_by="creation desc",
		start=start,
		page_length=size,
	)
	total = len(frappe.get_all("Freight Request", filters=filters, or_filters=or_filters, pluck="name"))
	counts = dict(frappe.db.sql("select status, count(*) from `tabFreight Request` group by status"))
	return {"items": items, "total": total, "counts": counts}


@frappe.whitelist(methods=["GET"])
def get_request(name: str):
	_require_admin()
	doc = frappe.get_doc("Freight Request", name)
	return {
		"request": request_full(doc),
		"customer": doc.customer,
		"customer_name": doc.customer_name,
		"published_on": doc.published_on,
		"booked_on": doc.booked_on,
		"cancel_reason": doc.cancel_reason,
		"leads_sent": doc.leads_sent,
		"unlock_count": doc.unlock_count,
		"leads": frappe.db.sql(
			"""select l.name, l.forwarder, f.company_name, l.status, l.sent_on, l.seen_on, l.unlocked_on,
				l.unlock_fee, l.was_free, l.decline_reason
			from `tabFreight Request Lead` l left join `tabSokan Forwarder` f on f.name=l.forwarder
			where l.request=%s order by l.unlocked_on is null, l.unlocked_on desc, f.company_name""",
			name,
			as_dict=True,
		),
		"quotes": [
			quote_payload(frappe.get_doc("Freight Quote", q))
			for q in frappe.get_all(
				"Freight Quote", {"request": name}, pluck="name", order_by="total_amount asc"
			)
		],
		"review": frappe.db.get_value(
			"Sokan Review", {"request": name}, ["name", "rating", "comment", "status"], as_dict=True
		),
	}


@frappe.whitelist(methods=["POST"])
def cancel_request(name: str, reason: str):
	_require_admin()
	if not (reason or "").strip():
		frappe.throw(_("Please give a reason. The customer will see it."))
	doc = frappe.get_doc("Freight Request", name)
	if doc.status not in ("Draft", "Open"):
		frappe.throw(_("Only draft or open requests can be cancelled."))
	doc.status = "Cancelled"
	doc.cancel_reason = _("Cancelled by Sokan: {0}").format(reason.strip())
	doc.save(ignore_permissions=True)
	from sokan.notifications import notify_request_cancelled_by_admin

	notify_request_cancelled_by_admin(name, reason.strip())
	return get_request(name)


# ---------------------------------------------------------------- top-ups


@frappe.whitelist(methods=["GET"])
def list_topups(status: str | None = "Pending", page: int = 1, page_size: int = 20):
	_require_admin()
	start, size = _paging(page, page_size)
	filters = {"status": status} if status else {}
	items = frappe.db.sql(
		f"""select t.name, t.forwarder, f.company_name, f.wallet_balance, t.amount, t.currency, t.status,
			t.payment_method, t.payment_reference, t.receipt, t.note, t.reviewed_by, t.reviewed_on, t.creation
		from `tabSokan Top Up` t left join `tabSokan Forwarder` f on f.name=t.forwarder
		{"where t.status=%(status)s" if status else ""}
		order by t.status='Pending' desc, t.creation desc limit %(start)s, %(size)s""",
		{"status": status, "start": start, "size": size},
		as_dict=True,
	)
	counts = dict(frappe.db.sql("select status, count(*) from `tabSokan Top Up` group by status"))
	return {"items": items, "total": frappe.db.count("Sokan Top Up", filters), "counts": counts}


@frappe.whitelist(methods=["POST"])
def review_topup(name: str, action: str, note: str | None = None):
	_require_admin()
	if action not in ("approve", "reject"):
		frappe.throw(_("Unknown action."))
	doc = frappe.get_doc("Sokan Top Up", name, for_update=True)
	if doc.status != "Pending":
		frappe.throw(_("This top-up was already {0}.").format(_(doc.status).lower()))
	if action == "reject" and not (note or "").strip():
		frappe.throw(_("Please give a reason. The company will see it."))
	doc.status = "Approved" if action == "approve" else "Rejected"
	if note:
		doc.note = note.strip()
	# Approving posts the ledger credit in the controller.
	doc.save(ignore_permissions=True)
	return {"name": doc.name, "status": doc.status}


# ---------------------------------------------------------------- reviews


@frappe.whitelist(methods=["GET"])
def list_reviews(status: str | None = "Pending", page: int = 1, page_size: int = 20):
	_require_admin()
	start, size = _paging(page, page_size)
	items = frappe.db.sql(
		f"""select r.name, r.forwarder, f.company_name, r.request, r.customer, r.customer_name, r.rating,
			r.comment, r.status, r.moderated_by, r.moderated_on, r.moderation_note, r.creation
		from `tabSokan Review` r left join `tabSokan Forwarder` f on f.name=r.forwarder
		{"where r.status=%(status)s" if status else ""}
		order by r.creation desc limit %(start)s, %(size)s""",
		{"status": status, "start": start, "size": size},
		as_dict=True,
	)
	counts = dict(frappe.db.sql("select status, count(*) from `tabSokan Review` group by status"))
	return {
		"items": items,
		"total": frappe.db.count("Sokan Review", {"status": status} if status else {}),
		"counts": counts,
	}


@frappe.whitelist(methods=["POST"])
def moderate_review(name: str, action: str, note: str | None = None):
	_require_admin()
	if action not in ("approve", "reject"):
		frappe.throw(_("Unknown action."))
	doc = frappe.get_doc("Sokan Review", name)
	was_approved = doc.status == "Approved"
	doc.status = "Approved" if action == "approve" else "Rejected"
	doc.moderated_by = frappe.session.user
	doc.moderated_on = now_datetime()
	doc.moderation_note = (note or "").strip() or None
	# Saving recomputes the forwarder's public rating from approved reviews.
	doc.save(ignore_permissions=True)
	if doc.status == "Approved" and not was_approved:
		from sokan.notifications import notify_review_published

		notify_review_published(doc)
	return {"name": doc.name, "status": doc.status}


# ---------------------------------------------------------------- messages


@frappe.whitelist(methods=["GET"])
def list_messages(status: str | None = "New", page: int = 1, page_size: int = 20):
	_require_admin()
	start, size = _paging(page, page_size)
	filters = {"status": status} if status else {}
	items = frappe.get_all(
		"Sokan Contact Message",
		filters=filters,
		fields=[
			"name",
			"full_name",
			"email",
			"phone",
			"company",
			"audience",
			"status",
			"subject",
			"message",
			"creation",
		],
		order_by="creation desc",
		start=start,
		page_length=size,
	)
	counts = dict(frappe.db.sql("select status, count(*) from `tabSokan Contact Message` group by status"))
	return {"items": items, "total": frappe.db.count("Sokan Contact Message", filters), "counts": counts}


@frappe.whitelist(methods=["POST"])
def set_message_status(name: str, status: str):
	_require_admin()
	if status not in ("New", "Replied", "Closed"):
		frappe.throw(_("Unknown status."))
	frappe.db.set_value("Sokan Contact Message", name, "status", status)
	return {"name": name, "status": status}


# ---------------------------------------------------------------- finance


@frappe.whitelist(methods=["GET"])
def list_transactions(
	forwarder: str | None = None,
	transaction_type: str | None = None,
	from_date: str | None = None,
	to_date: str | None = None,
	page: int = 1,
	page_size: int = 50,
):
	_require_admin()
	start, size = _paging(page, page_size, default=50)
	cond, args = ["1=1"], {"start": start, "size": size}
	if forwarder:
		cond.append("t.forwarder=%(forwarder)s")
		args["forwarder"] = forwarder
	if transaction_type:
		cond.append("t.transaction_type=%(type)s")
		args["type"] = transaction_type
	if from_date:
		cond.append("date(t.posting_date) >= %(from)s")
		args["from"] = getdate(from_date)
	if to_date:
		cond.append("date(t.posting_date) <= %(to)s")
		args["to"] = getdate(to_date)
	where = " and ".join(cond)
	items = frappe.db.sql(
		f"""select t.name, t.forwarder, f.company_name, t.transaction_type, t.amount, t.balance_after,
			t.currency, t.posting_date, t.description, t.reference_doctype, t.reference_name
		from `tabSokan Wallet Transaction` t left join `tabSokan Forwarder` f on f.name=t.forwarder
		where {where} order by t.posting_date desc limit %(start)s, %(size)s""",
		args,
		as_dict=True,
	)
	total, credits, debits = frappe.db.sql(
		f"""select count(*), coalesce(sum(case when t.amount > 0 then t.amount end), 0),
			coalesce(sum(case when t.amount < 0 then t.amount end), 0)
		from `tabSokan Wallet Transaction` t where {where}""",
		args,
	)[0]
	return {
		"items": items,
		"total": total,
		"credits": flt(credits),
		"debits": flt(debits),
		"currency": platform_currency(),
	}


# ---------------------------------------------------------------- catalogue


PLAN_EDITABLE = {
	"is_active": bool,
	"is_default": bool,
	"badge": str,
	"currency": str,
	"sort_order": int,
	"monthly_fee": float,
	"view_fee": float,
	"quote_fee": float,
	"free_views_per_month": int,
	"free_quotes_per_month": int,
	"priority_listing": bool,
	"description": str,
}


@frappe.whitelist(methods=["GET"])
def list_plans():
	_require_admin()
	plans = frappe.get_all(
		"Sokan Plan", fields=["name", "plan_name", *PLAN_EDITABLE.keys()], order_by="sort_order asc"
	)
	subscribers = dict(frappe.db.sql("select plan, count(*) from `tabSokan Forwarder` group by plan"))
	for p in plans:
		p["features"] = frappe.get_all(
			"Sokan Plan Feature",
			filters={"parent": p.name, "parenttype": "Sokan Plan"},
			pluck="feature",
			order_by="idx",
		)
		p["subscribers"] = subscribers.get(p.name, 0)
	return plans


@frappe.whitelist(methods=["POST"])
def save_plan(data: dict | str):
	_require_admin()
	data = frappe.parse_json(data) or {}
	name = (data.get("name") or "").strip()
	doc = frappe.get_doc("Sokan Plan", name) if name else frappe.new_doc("Sokan Plan")
	if doc.is_new():
		doc.plan_name = (data.get("plan_name") or "").strip()
		if not doc.plan_name:
			frappe.throw(_("Plan name is required."))
	values = _clean(data, PLAN_EDITABLE)
	for fee in ("monthly_fee", "view_fee", "quote_fee", "free_views_per_month", "free_quotes_per_month"):
		if values.get(fee, 0) < 0:
			frappe.throw(_("Fees and allowances cannot be negative."))
	doc.update(values)
	if isinstance(data.get("features"), list):
		doc.set("features", [{"feature": str(f).strip()} for f in data["features"] if str(f).strip()])
	doc.save(ignore_permissions=True)
	if doc.is_default:
		# Exactly one default plan: new forwarders start on it.
		frappe.db.sql("update `tabSokan Plan` set is_default=0 where name!=%s", doc.name)
	frappe.cache.delete_value("sokan:home")
	return list_plans()


MODE_EDITABLE = {"is_active": bool, "sort_order": int, "description": str, "icon": str}


@frappe.whitelist(methods=["GET"])
def list_modes():
	_require_admin()
	modes = frappe.get_all(
		"Sokan Transport Mode",
		fields=[
			"name",
			"mode_name",
			"code",
			"category",
			"icon",
			"sort_order",
			"is_active",
			"uses_containers",
			"description",
		],
		order_by="sort_order asc",
	)
	usage = dict(
		frappe.db.sql("select transport_mode, count(*) from `tabFreight Request` group by transport_mode")
	)
	for m in modes:
		m["requests"] = usage.get(m.name, 0)
	return modes


@frappe.whitelist(methods=["POST"])
def save_mode(name: str, data: dict | str):
	_require_admin()
	doc = frappe.get_doc("Sokan Transport Mode", name)
	doc.update(_clean(data, MODE_EDITABLE))
	doc.save(ignore_permissions=True)
	frappe.cache.delete_value("sokan:home")
	return list_modes()


# ---------------------------------------------------------------- settings

SETTINGS_EDITABLE = {
	"platform_name": str,
	"support_email": str,
	"support_phone": str,
	"frontend_url": str,
	"default_currency": str,
	"default_view_fee": float,
	"default_quote_fee": float,
	"signup_bonus": float,
	"low_balance_threshold": float,
	"refund_unlock_if_cancelled": bool,
	"topup_instructions": str,
	"match_transport_mode": bool,
	"match_coverage": bool,
	"auto_publish_requests": bool,
	"auto_approve_forwarders": bool,
	"request_validity_days": int,
	"max_quotes_per_request": int,
}


@frappe.whitelist(methods=["GET"])
def get_settings():
	_require_admin()
	doc = frappe.get_single("Sokan Settings")
	return {k: doc.get(k) for k in SETTINGS_EDITABLE}


@frappe.whitelist(methods=["POST"])
def update_settings(data: dict | str):
	_require_admin()
	values = _clean(data, SETTINGS_EDITABLE)
	for k in ("default_view_fee", "default_quote_fee", "signup_bonus", "low_balance_threshold"):
		if values.get(k, 0) < 0:
			frappe.throw(_("Fees and amounts cannot be negative."))
	if "request_validity_days" in values and not 1 <= values["request_validity_days"] <= 365:
		frappe.throw(_("Request validity must be between 1 and 365 days."))
	doc = frappe.get_single("Sokan Settings")
	doc.update(values)
	doc.save(ignore_permissions=True)
	return get_settings()


# ---------------------------------------------------------------- managers


@frappe.whitelist(methods=["GET"])
def list_managers():
	_require_admin()
	users = frappe.get_all("Has Role", {"role": ROLE_ADMIN, "parenttype": "User"}, pluck="parent")
	return frappe.get_all(
		"User",
		filters={"name": ("in", users or [""])},
		fields=["name", "full_name", "enabled", "last_login", "creation"],
		order_by="full_name asc",
	)


@frappe.whitelist(methods=["POST"])
def add_manager(email: str, full_name: str | None = None):
	"""Give someone manager access, creating a portal-only account if needed."""
	_require_admin()
	email = (email or "").strip().lower()
	frappe.utils.validate_email_address(email, throw=True)
	new_account = not frappe.db.exists("User", email)
	if not new_account:
		add_role(email, ROLE_ADMIN)
	else:
		first, _sep, last = (full_name or email.split("@")[0]).strip().partition(" ")
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": first,
				"last_name": last or None,
				# Website User: signs in to the Nuxt portal, never to Desk.
				"user_type": "Website User",
				# Sokan sends its own invitation (below) linking to the website, not Desk.
				"send_welcome_email": 0,
				"roles": [{"role": ROLE_ADMIN}],
			}
		)
		user.flags.ignore_permissions = True
		user.insert()
	from sokan.notifications import notify_manager_invite

	notify_manager_invite(email, new_account)
	return list_managers()


@frappe.whitelist(methods=["POST"])
def remove_manager(user: str):
	_require_admin()
	if user == frappe.session.user:
		frappe.throw(_("You cannot remove your own manager access."))
	if user == "Administrator":
		frappe.throw(_("The Administrator account cannot be changed here."))
	doc = frappe.get_doc("User", user)
	doc.flags.ignore_permissions = True
	doc.remove_roles(ROLE_ADMIN)
	return list_managers()
