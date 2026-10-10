"""Fan a published Freight Request out to every matching forwarder.

“Matching” is controlled by Sokan Settings:

* match_transport_mode — the forwarder lists the request's mode in Services;
* match_coverage       — the forwarder's coverage is empty (worldwide) or
                         includes the origin or destination country.

Each match gets one Freight Request Lead. Leads are free to receive; the
forwarder pays only when they unlock one (see sokan.billing).
"""

import frappe
from frappe.utils import now_datetime

from sokan.utils import get_settings

# Above this many forwarders the fan-out moves to a background job so the
# customer's "Publish" click returns immediately.
INLINE_LIMIT = 40


def matching_forwarders(request) -> list[str]:
	settings = get_settings()
	Fwd = frappe.qb.DocType("Sokan Forwarder")
	query = frappe.qb.from_(Fwd).select(Fwd.name).where(Fwd.status == "Active")

	if settings.match_transport_mode:
		Svc = frappe.qb.DocType("Sokan Forwarder Service")
		query = query.where(
			Fwd.name.isin(
				frappe.qb.from_(Svc)
				.select(Svc.parent)
				.where((Svc.parenttype == "Sokan Forwarder") & (Svc.transport_mode == request.transport_mode))
			)
		)

	names = [r[0] for r in query.run()]

	if settings.match_coverage and names:
		coverage: dict[str, set[str]] = {}
		for row in frappe.get_all(
			"Sokan Forwarder Country",
			filters={"parenttype": "Sokan Forwarder", "parent": ("in", names)},
			fields=["parent", "country"],
		):
			coverage.setdefault(row.parent, set()).add(row.country)
		lane = {request.origin_country, request.destination_country}
		names = [n for n in names if n not in coverage or coverage[n] & lane]

	return names


def distribute(request_name: str):
	request = frappe.get_doc("Freight Request", request_name)
	targets = matching_forwarders(request)
	if len(targets) > INLINE_LIMIT and not frappe.flags.in_test:
		frappe.enqueue(
			"sokan.distribution.create_leads",
			queue="short",
			request_name=request_name,
			forwarders=targets,
			enqueue_after_commit=True,
		)
	else:
		create_leads(request_name, targets)


def create_leads(request_name: str, forwarders: list[str]):
	existing = set(frappe.get_all("Freight Request Lead", {"request": request_name}, pluck="forwarder"))
	created = []
	now = now_datetime()
	for fwd in forwarders:
		if fwd in existing:
			continue
		lead = frappe.get_doc(
			{"doctype": "Freight Request Lead", "request": request_name, "forwarder": fwd, "sent_on": now}
		)
		lead.insert(ignore_permissions=True)
		created.append(fwd)

	if created:
		Fwd = frappe.qb.DocType("Sokan Forwarder")
		frappe.qb.update(Fwd).set(Fwd.leads_received, Fwd.leads_received + 1).where(
			Fwd.name.isin(created)
		).run()

	total = frappe.db.count("Freight Request Lead", {"request": request_name})
	frappe.db.set_value("Freight Request", request_name, "leads_sent", total, update_modified=False)

	from sokan.notifications import notify_new_leads

	notify_new_leads(request_name, created)
