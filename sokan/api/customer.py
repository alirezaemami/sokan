"""Customer (shipper) portal endpoints. Every call is scoped to the caller's own Sokan Customer."""

import frappe
from frappe import _
from frappe.utils import cint, now_datetime

from sokan.api.serializers import quote_payload, request_full, request_teaser
from sokan.utils import customer_for_user, get_settings, require_login
from sokan.verification import is_verified, require_verified

REQUEST_FIELDS = {
	"transport_mode",
	"incoterm",
	"origin_country",
	"origin_city",
	"origin_port",
	"pickup_required",
	"pickup_address",
	"destination_country",
	"destination_city",
	"destination_port",
	"delivery_required",
	"delivery_address",
	"ready_date",
	"valid_until",
	"commodity",
	"hs_code",
	"cargo_category",
	"is_stackable",
	"cargo_value",
	"cargo_currency",
	"un_number",
	"temperature_range",
	"total_weight_kg",
	"total_volume_cbm",
	"need_customs_clearance",
	"need_insurance",
	"need_warehousing",
	"need_packing",
	"quote_currency",
	"notes",
	"attachment",
	"contact_name",
	"contact_email",
	"contact_phone",
	"contact_company",
}
PACKAGE_FIELDS = {"package_type", "quantity", "length_cm", "width_cm", "height_cm", "weight_kg"}
CONTAINER_FIELDS = {"container_type", "quantity", "weight_kg", "is_shipper_owned"}


def _customer() -> str:
	require_login()
	return customer_for_user()


def _own_request(name: str):
	doc = frappe.get_doc("Freight Request", name)
	if doc.customer != _customer():
		raise frappe.PermissionError(_("Not your request."))
	return doc


@frappe.whitelist(methods=["GET"])
def dashboard():
	cust = _customer()
	counts = dict(
		frappe.db.sql(
			"select status, count(*) from `tabFreight Request` where customer=%s group by status", cust
		)
	)
	recent = frappe.get_all(
		"Freight Request", {"customer": cust}, pluck="name", order_by="creation desc", limit=5
	)
	return {
		"counts": counts,
		"quotes_waiting": frappe.db.count(
			"Freight Quote",
			{
				"status": "Submitted",
				"request": (
					"in",
					frappe.get_all("Freight Request", {"customer": cust, "status": "Open"}, pluck="name")
					or [""],
				),
			},
		),
		"recent": [_list_row(frappe.get_doc("Freight Request", n)) for n in recent],
	}


def _list_row(doc) -> dict:
	row = request_teaser(doc)
	best = frappe.get_all(
		"Freight Quote",
		{"request": doc.name, "status": ("in", ("Submitted", "Accepted"))},
		["total_amount", "currency"],
		order_by="total_amount asc",
		limit=1,
	)
	row["best_quote"] = best[0] if best else None
	row["leads_sent"] = doc.leads_sent
	row["unlock_count"] = doc.unlock_count
	row["creation"] = doc.creation
	return row


@frappe.whitelist(methods=["GET"])
def list_requests(status: str | None = None, page: int = 1, page_size: int = 20):
	cust = _customer()
	filters = {"customer": cust}
	if status:
		filters["status"] = status
	page, page_size = max(cint(page), 1), min(max(cint(page_size), 1), 50)
	names = frappe.get_all(
		"Freight Request",
		filters,
		pluck="name",
		order_by="creation desc",
		limit=page_size,
		start=(page - 1) * page_size,
	)
	return {
		"items": [_list_row(frappe.get_doc("Freight Request", n)) for n in names],
		"total": frappe.db.count("Freight Request", filters),
	}


@frappe.whitelist(methods=["POST"])
def create_request(data: dict | str, publish: int = 1):
	cust = _customer()
	if frappe.db.get_value("Sokan Customer", cust, "is_blocked"):
		frappe.throw(_("Your account cannot publish requests. Please contact support."))
	data = frappe.parse_json(data)

	doc = frappe.new_doc("Freight Request")
	doc.customer = cust
	for k in REQUEST_FIELDS & set(data):
		doc.set(k, data[k])
	for p in data.get("packages") or []:
		doc.append("packages", {k: p.get(k) for k in PACKAGE_FIELDS})
	for c in data.get("containers") or []:
		doc.append("containers", {k: c.get(k) for k in CONTAINER_FIELDS})

	# An unconfirmed email keeps the request a draft: the form isn't lost, and it
	# is published once the shipper enters their code.
	needs_verification = bool(cint(publish)) and not is_verified()
	if cint(publish) and not needs_verification:
		doc.status = "Open" if get_settings().auto_publish_requests else "Draft"
	doc.insert(ignore_permissions=True)
	frappe.db.set_value(
		"Sokan Customer", cust, "requests_count", frappe.db.count("Freight Request", {"customer": cust})
	)
	return {
		"name": doc.name,
		"status": doc.status,
		"leads_sent": frappe.db.get_value("Freight Request", doc.name, "leads_sent"),
		"needs_verification": needs_verification,
	}


@frappe.whitelist(methods=["GET"])
def get_request(name: str):
	doc = _own_request(name)
	quotes = [
		quote_payload(frappe.get_doc("Freight Quote", q))
		for q in frappe.get_all(
			"Freight Quote",
			{"request": name, "status": ("!=", "Withdrawn")},
			pluck="name",
			order_by="total_amount asc",
		)
	]
	# Priority-plan forwarders float up among equals; price still dominates.
	quotes.sort(key=lambda q: (q["status"] != "Accepted", q["total_amount"], not q["priority"]))
	# Booking is the moment both sides get each other's contact details.
	for q in quotes:
		if q["status"] == "Accepted":
			q["forwarder"]["contact"] = frappe.db.get_value(
				"Sokan Forwarder",
				q["forwarder"]["name"],
				["email", "phone", "website", "address"],
				as_dict=True,
			)
	review = frappe.db.get_value(
		"Sokan Review", {"request": name}, ["rating", "comment", "status"], as_dict=True
	)
	return {
		"request": request_full(doc),
		"leads_sent": doc.leads_sent,
		"unlock_count": doc.unlock_count,
		"accepted_quote": doc.accepted_quote,
		"cancel_reason": doc.cancel_reason,
		"quotes": quotes,
		"review": review,
	}


@frappe.whitelist(methods=["POST"])
def accept_quote(quote: str):
	q = frappe.get_doc("Freight Quote", quote)
	# Lock first, then read: two simultaneous accepts must not both book.
	frappe.db.sql("select name from `tabFreight Request` where name=%s for update", q.request)
	q.reload()
	req = _own_request(q.request)
	if req.status != "Open":
		frappe.throw(_("This request is {0} and can no longer be booked.").format(_(req.status)))
	if q.status != "Submitted":
		frappe.throw(_("This quote is {0}.").format(_(q.status)))

	now = now_datetime()
	q.db_set({"status": "Accepted", "accepted_on": now})
	req.db_set({"status": "Booked", "accepted_quote": q.name, "booked_on": now})

	from sokan.notifications import notify_booking, notify_quote_rejected

	for other in frappe.get_all(
		"Freight Quote", {"request": req.name, "status": "Submitted", "name": ("!=", q.name)}, pluck="name"
	):
		o = frappe.get_doc("Freight Quote", other)
		o.db_set({"status": "Rejected", "rejection_reason": _("Customer booked another quote")})
		notify_quote_rejected(o)
	frappe.db.set_value(
		"Freight Request Lead",
		{"request": req.name, "status": ("in", ("New", "Unlocked"))},
		"status",
		"Closed",
	)

	Fwd = frappe.qb.DocType("Sokan Forwarder")
	frappe.qb.update(Fwd).set(Fwd.quotes_won, Fwd.quotes_won + 1).where(Fwd.name == q.forwarder).run()
	frappe.db.set_value(
		"Sokan Customer",
		req.customer,
		"bookings_count",
		frappe.db.count("Freight Request", {"customer": req.customer, "status": "Booked"}),
	)
	notify_booking(q)
	return get_request(req.name)


@frappe.whitelist(methods=["POST"])
def reject_quote(quote: str, reason: str | None = None):
	q = frappe.get_doc("Freight Quote", quote)
	_own_request(q.request)
	if q.status != "Submitted":
		frappe.throw(_("This quote is {0}.").format(_(q.status)))
	q.db_set({"status": "Rejected", "rejection_reason": reason})
	from sokan.notifications import notify_quote_rejected

	notify_quote_rejected(q, reason)
	return get_request(q.request)


@frappe.whitelist(methods=["POST"])
def cancel_request(name: str, reason: str | None = None):
	doc = _own_request(name)
	if doc.status not in ("Draft", "Open"):
		frappe.throw(_("Only draft or open requests can be cancelled."))
	doc.status = "Cancelled"
	doc.cancel_reason = reason
	doc.save(ignore_permissions=True)
	return get_request(name)


@frappe.whitelist(methods=["POST"])
def publish_request(name: str):
	doc = _own_request(name)
	if doc.status != "Draft":
		frappe.throw(_("Only drafts can be published."))
	require_verified()
	doc.status = "Open"
	doc.save(ignore_permissions=True)
	return get_request(name)


@frappe.whitelist(methods=["POST"])
def leave_review(request: str, rating: int, comment: str | None = None):
	req = _own_request(request)
	if req.status != "Booked" or not req.accepted_quote:
		frappe.throw(_("You can review a forwarder after booking them."))
	forwarder = frappe.db.get_value("Freight Quote", req.accepted_quote, "forwarder")
	existing = frappe.db.get_value("Sokan Review", {"request": request}, "name")
	doc = frappe.get_doc("Sokan Review", existing) if existing else frappe.new_doc("Sokan Review")
	doc.update(
		{
			"forwarder": forwarder,
			"request": request,
			"customer": req.customer,
			"rating": cint(rating),
			"comment": comment,
			# New or edited, a review waits for a manager before it is public.
			"status": "Pending",
			"moderated_by": None,
			"moderated_on": None,
		}
	)
	doc.save(ignore_permissions=True)
	from sokan.notifications import notify_admin_new_review

	notify_admin_new_review(doc)
	return {"rating": doc.rating, "comment": doc.comment, "status": doc.status}


@frappe.whitelist(methods=["GET"])
def get_profile():
	return frappe.get_doc("Sokan Customer", _customer()).as_dict(
		no_default_fields=True, no_child_table_fields=True
	)


@frappe.whitelist(methods=["POST"])
def update_profile(data: dict | str):
	data = frappe.parse_json(data)
	doc = frappe.get_doc("Sokan Customer", _customer())
	for k in ("full_name", "phone", "company_name", "country", "city", "customer_type"):
		if k in data:
			doc.set(k, data[k])
	doc.save(ignore_permissions=True)
	return get_profile()
