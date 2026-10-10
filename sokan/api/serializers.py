"""Shape documents for the website.

The split between ``request_teaser`` and ``request_full`` is the product:
everything in the teaser is what a forwarder sees for free; everything only in
the full payload (exact addresses, packing details, notes, attachment and the
customer's identity) is what they pay to unlock.
"""

import frappe
from frappe.utils import flt


def country_codes() -> dict[str, str]:
	def load():
		return {r.name: (r.code or "").upper() for r in frappe.get_all("Country", fields=["name", "code"])}

	return frappe.cache.get_value("sokan:country_codes", load)


def place(city, country, port=None) -> dict:
	return {"city": city, "country": country, "country_code": country_codes().get(country), "port": port}


def mode_info(name: str | None) -> dict | None:
	if not name:
		return None
	m = frappe.get_cached_value(
		"Sokan Transport Mode", name, ["name", "code", "category", "icon", "uses_containers"], as_dict=True
	)
	return m


def cargo_summary(doc) -> dict:
	containers = [
		{"type": c.container_type, "qty": int(c.quantity or 0), "weight_kg": flt(c.weight_kg)}
		for c in doc.containers
	]
	return {
		"commodity": doc.commodity,
		"category": doc.cargo_category,
		"containers": containers,
		"total_packages": int(doc.total_packages or 0),
		"total_weight_kg": flt(doc.total_weight_kg),
		"total_volume_cbm": flt(doc.total_volume_cbm),
		"chargeable_weight_kg": flt(doc.chargeable_weight_kg),
		"is_stackable": bool(doc.is_stackable),
	}


def request_teaser(doc) -> dict:
	return {
		"name": doc.name,
		"title": doc.title,
		"status": doc.status,
		"mode": mode_info(doc.transport_mode),
		"incoterm": doc.incoterm,
		"origin": place(doc.origin_city, doc.origin_country),
		"destination": place(doc.destination_city, doc.destination_country),
		"pickup_required": bool(doc.pickup_required),
		"delivery_required": bool(doc.delivery_required),
		"ready_date": doc.ready_date,
		"valid_until": doc.valid_until,
		"published_on": doc.published_on,
		"cargo": cargo_summary(doc),
		"services": {
			"customs": bool(doc.need_customs_clearance),
			"insurance": bool(doc.need_insurance),
			"warehousing": bool(doc.need_warehousing),
			"packing": bool(doc.need_packing),
		},
		"quote_count": int(doc.quote_count or 0),
		"quote_currency": doc.quote_currency,
	}


def request_full(doc) -> dict:
	data = request_teaser(doc)
	data["origin"] = place(doc.origin_city, doc.origin_country, doc.origin_port)
	data["destination"] = place(doc.destination_city, doc.destination_country, doc.destination_port)
	data.update(
		{
			"pickup_address": doc.pickup_address,
			"delivery_address": doc.delivery_address,
			"hs_code": doc.hs_code,
			"un_number": doc.un_number,
			"temperature_range": doc.temperature_range,
			"cargo_value": flt(doc.cargo_value),
			"cargo_currency": doc.cargo_currency,
			"packages": [
				{
					"type": p.package_type,
					"qty": int(p.quantity or 0),
					"length_cm": flt(p.length_cm),
					"width_cm": flt(p.width_cm),
					"height_cm": flt(p.height_cm),
					"weight_kg": flt(p.weight_kg),
					"volume_cbm": flt(p.volume_cbm),
				}
				for p in doc.packages
			],
			"notes": doc.notes,
			"attachment": doc.attachment,
			"contact": {
				"name": doc.contact_name,
				"email": doc.contact_email,
				"phone": doc.contact_phone,
				"company": doc.contact_company,
			},
		}
	)
	return data


def forwarder_card(f) -> dict:
	"""Public, directory-level view of a forwarder. `f` is a dict or doc."""
	return {
		"name": f.get("name"),
		"slug": f.get("slug"),
		"company_name": f.get("company_name"),
		"tagline": f.get("tagline"),
		"logo": f.get("logo"),
		"country": f.get("country"),
		"country_code": country_codes().get(f.get("country")),
		"city": f.get("city"),
		"is_verified": bool(f.get("is_verified")),
		"rating": flt(f.get("rating")),
		"review_count": int(f.get("review_count") or 0),
		"established_year": f.get("established_year"),
	}


def quote_payload(q, *, include_forwarder: bool = True) -> dict:
	data = {
		"name": q.name,
		"request": q.request,
		"status": q.status,
		"currency": q.currency,
		"total_amount": flt(q.total_amount),
		"transit_days_min": q.transit_days_min,
		"transit_days_max": q.transit_days_max,
		"valid_until": q.valid_until,
		"carrier": q.carrier,
		"routing": q.routing,
		"free_days": q.free_days,
		"service_level": q.service_level,
		"inclusions": q.inclusions,
		"exclusions": q.exclusions,
		"notes": q.notes,
		"creation": q.creation,
		"charges": [
			{
				"group": c.charge_group,
				"description": c.description,
				"basis": c.basis,
				"quantity": flt(c.quantity),
				"unit_price": flt(c.unit_price),
				"amount": flt(c.amount),
			}
			for c in q.charges
		],
	}
	if include_forwarder:
		f = frappe.db.get_value(
			"Sokan Forwarder",
			q.forwarder,
			[
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
				"plan",
			],
			as_dict=True,
		)
		data["forwarder"] = forwarder_card(f)
		data["priority"] = bool(f.plan and frappe.get_cached_value("Sokan Plan", f.plan, "priority_listing"))
	return data
