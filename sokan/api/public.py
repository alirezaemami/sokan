"""Guest endpoints behind the marketing site, directory and sitemap."""

import frappe
from frappe import _
from frappe.query_builder.functions import Count
from frappe.rate_limiter import rate_limit
from frappe.utils import cint, strip_html

from sokan.api.serializers import country_codes, forwarder_card, mode_info, place

FORWARDER_CARD_FIELDS = [
	"name",
	"slug",
	"company_name",
	"tagline",
	"logo",
	"country",
	"city",
	"is_verified",
	"rating",
	"review_count",
	"established_year",
]


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_home():
	def build():
		return {
			"stats": get_stats(),
			"modes": list_transport_modes(),
			"featured": _cards(
				frappe.get_all(
					"Sokan Forwarder",
					filters={"status": "Active"},
					fields=FORWARDER_CARD_FIELDS,
					order_by="is_featured desc, is_verified desc, rating desc, quotes_won desc",
					limit=8,
				)
			),
			"live": recent_requests(),
			"plans": list_plans(),
		}

	# Home is hit by every visitor and crawler; a short cache keeps it cheap
	# without the live ticker going stale.
	data = frappe.cache.get_value("sokan:home")
	if data is None:
		data = build()
		frappe.cache.set_value("sokan:home", data, expires_in_sec=120)
	return data


def get_stats() -> dict:
	return {
		"forwarders": frappe.db.count("Sokan Forwarder", {"status": "Active"}),
		"requests": frappe.db.count("Freight Request", {"status": ("not in", ("Draft",))}),
		"quotes": frappe.db.count("Freight Quote"),
		"countries": len(
			{r[0] for r in frappe.db.sql("select distinct origin_country from `tabFreight Request`")}
			| {r[0] for r in frappe.db.sql("select distinct destination_country from `tabFreight Request`")}
		),
	}


def recent_requests(limit: int = 12) -> list[dict]:
	"""Anonymised feed for the home-page ticker — lanes and modes only, never who or what exactly."""
	rows = frappe.get_all(
		"Freight Request",
		filters={"status": ("in", ("Open", "Booked"))},
		fields=[
			"origin_city",
			"origin_country",
			"destination_city",
			"destination_country",
			"transport_mode",
			"cargo_category",
			"published_on",
			"quote_count",
			"status",
		],
		order_by="published_on desc",
		limit=limit,
	)
	return [
		{
			"origin": place(r.origin_city, r.origin_country),
			"destination": place(r.destination_city, r.destination_country),
			"mode": mode_info(r.transport_mode),
			"category": r.cargo_category,
			"published_on": r.published_on,
			"quote_count": r.quote_count,
			"status": r.status,
		}
		for r in rows
	]


@frappe.whitelist(allow_guest=True, methods=["GET"])
def list_transport_modes():
	return frappe.get_all(
		"Sokan Transport Mode",
		filters={"is_active": 1},
		fields=["name", "code", "category", "icon", "uses_containers", "description"],
		order_by="sort_order asc",
	)


@frappe.whitelist(allow_guest=True, methods=["GET"])
def list_plans():
	plans = frappe.get_all(
		"Sokan Plan",
		filters={"is_active": 1},
		fields=[
			"name",
			"badge",
			"currency",
			"monthly_fee",
			"view_fee",
			"quote_fee",
			"free_views_per_month",
			"free_quotes_per_month",
			"priority_listing",
			"description",
			"is_default",
		],
		order_by="sort_order asc",
	)
	features = {}
	for row in frappe.get_all(
		"Sokan Plan Feature",
		filters={"parenttype": "Sokan Plan"},
		fields=["parent", "feature"],
		order_by="idx asc",
	):
		features.setdefault(row.parent, []).append(row.feature)
	for p in plans:
		p["features"] = features.get(p.name, [])
	return plans


@frappe.whitelist(allow_guest=True, methods=["GET"])
def list_countries():
	return frappe.cache.get_value(
		"sokan:countries",
		lambda: [{"name": n, "code": c} for n, c in sorted(country_codes().items()) if c],
	)


@frappe.whitelist(allow_guest=True, methods=["GET"])
def list_forwarders(
	search: str | None = None,
	mode: str | None = None,
	country: str | None = None,
	page: int = 1,
	page_size: int = 12,
):
	page, page_size = max(cint(page), 1), min(max(cint(page_size), 1), 48)
	Fwd = frappe.qb.DocType("Sokan Forwarder")
	Plan = frappe.qb.DocType("Sokan Plan")
	q = frappe.qb.from_(Fwd).left_join(Plan).on(Plan.name == Fwd.plan).where(Fwd.status == "Active")
	if search:
		like = f"%{search.strip()}%"
		q = q.where(Fwd.company_name.like(like) | Fwd.city.like(like) | Fwd.tagline.like(like))
	if country:
		q = q.where(Fwd.country == country)
	if mode:
		Svc = frappe.qb.DocType("Sokan Forwarder Service")
		q = q.where(
			Fwd.name.isin(
				frappe.qb.from_(Svc)
				.select(Svc.parent)
				.where((Svc.parenttype == "Sokan Forwarder") & (Svc.transport_mode == mode))
			)
		)

	total = q.select(Count(Fwd.name)).run()[0][0]
	rows = (
		q.select(*[Fwd[f] for f in FORWARDER_CARD_FIELDS])
		.orderby(Plan.priority_listing, order=frappe.qb.desc)
		.orderby(Fwd.is_verified, order=frappe.qb.desc)
		.orderby(Fwd.rating, order=frappe.qb.desc)
		.orderby(Fwd.quotes_won, order=frappe.qb.desc)
		.limit(page_size)
		.offset((page - 1) * page_size)
		.run(as_dict=True)
	)
	return {"items": _cards(rows), "total": total, "page": page, "page_size": page_size}


def _cards(rows) -> list[dict]:
	"""Directory cards with each company's modes and its latest approved review."""
	names = [r.name for r in rows]
	services = _services_for(names)
	reviews = _latest_reviews(names)
	cards = []
	for r in rows:
		card = forwarder_card(r)
		card["modes"] = services.get(r.name, [])
		card["review"] = reviews.get(r.name)
		cards.append(card)
	return cards


def public_name(full_name: str | None) -> str:
	"""Reviewers are private individuals: publish first name and initial only."""
	parts = (full_name or "").split()
	return f"{parts[0]} {parts[-1][0]}." if len(parts) > 1 else (parts[0] if parts else "")


def _latest_reviews(names: list[str]) -> dict[str, dict]:
	"""The newest approved review with a written comment, per forwarder."""
	out: dict[str, dict] = {}
	if not names:
		return out
	for r in frappe.get_all(
		"Sokan Review",
		filters={"forwarder": ("in", names), "status": "Approved", "comment": ("is", "set")},
		fields=["forwarder", "customer_name", "rating", "comment", "creation"],
		order_by="creation desc",
	):
		if r.forwarder not in out:
			out[r.forwarder] = {
				"author": public_name(r.customer_name),
				"rating": r.rating,
				"comment": r.comment,
				"creation": r.creation,
			}
	return out


def _services_for(names: list[str]) -> dict[str, list[str]]:
	out: dict[str, list[str]] = {}
	if not names:
		return out
	for row in frappe.get_all(
		"Sokan Forwarder Service",
		filters={"parenttype": "Sokan Forwarder", "parent": ("in", names)},
		fields=["parent", "transport_mode"],
	):
		out.setdefault(row.parent, []).append(row.transport_mode)
	return out


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_forwarder(slug: str):
	name = frappe.db.get_value("Sokan Forwarder", {"slug": slug, "status": "Active"}, "name")
	if not name:
		raise frappe.DoesNotExistError(_("Forwarder not found"))
	f = frappe.get_doc("Sokan Forwarder", name)
	data = forwarder_card(f)
	data.update(
		{
			"about": f.about,
			"cover_image": f.cover_image,
			"website": f.website,
			"team_size": f.team_size,
			"certifications": [c.strip() for c in (f.certifications or "").splitlines() if c.strip()],
			"modes": [mode_info(s.transport_mode) for s in f.services],
			"coverage": [{"name": c.country, "code": country_codes().get(c.country)} for c in f.coverage],
			"stats": {
				"quotes_sent": f.quotes_sent,
				"quotes_won": f.quotes_won,
				"win_rate": round(100 * f.quotes_won / f.quotes_sent) if f.quotes_sent else None,
			},
			"meta_description": f.meta_description or strip_html(f.about or "")[:158] or f.tagline,
			"reviews": frappe.get_all(
				"Sokan Review",
				filters={"forwarder": name, "status": "Approved"},
				fields=["customer_name", "rating", "comment", "creation"],
				order_by="creation desc",
				limit=20,
			),
		}
	)
	for r in data["reviews"]:
		r.customer_name = public_name(r.customer_name)
	return data


@frappe.whitelist(allow_guest=True, methods=["GET"])
def sitemap_urls():
	return [
		{"slug": r.slug, "modified": r.modified}
		for r in frappe.get_all("Sokan Forwarder", {"status": "Active"}, ["slug", "modified"])
	]


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=5, seconds=60 * 60)
def submit_contact(
	full_name: str,
	email: str,
	message: str,
	phone: str | None = None,
	company: str | None = None,
	subject: str | None = None,
	audience: str = "Shipper",
):
	frappe.utils.validate_email_address(email, throw=True)
	if len((message or "").strip()) < 10:
		frappe.throw(_("Please write a little more so we can help."))
	doc = frappe.get_doc(
		{
			"doctype": "Sokan Contact Message",
			"full_name": full_name,
			"email": email,
			"phone": phone,
			"company": company,
			"subject": subject,
			"audience": audience if audience in ("Shipper", "Forwarder", "Partner", "Other") else "Other",
			"message": message,
		}
	).insert(ignore_permissions=True)
	return {"name": doc.name}
