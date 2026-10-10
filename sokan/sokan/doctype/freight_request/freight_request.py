import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, flt, getdate, now_datetime, nowdate, time_diff_in_hours

# Volumetric divisors (kg per CBM) used to derive chargeable weight.
VOLUMETRIC_KG_PER_CBM = {"Air": 167, "Courier": 200, "Road": 333, "Rail": 333}

CONTAINER_TEU = {"20": 1, "40": 2, "45": 2}


class FreightRequest(Document):
	"""A customer's request for freight prices. Publishing it fans out one Freight Request Lead per matching forwarder."""

	def validate(self):
		self.compute_totals()
		self.set_title()
		self.set_contact_defaults()
		self.validate_route()
		if self.status == "Open" and not self.valid_until:
			days = frappe.db.get_single_value("Sokan Settings", "request_validity_days") or 14
			self.valid_until = add_days(nowdate(), days)
		if self.status == "Open" and not self.published_on and getdate(self.valid_until) < getdate(nowdate()):
			frappe.throw(_("“Accept quotes until” must be today or later."))

	def compute_totals(self):
		mode = (
			frappe.get_cached_value(
				"Sokan Transport Mode", self.transport_mode, ["category", "uses_containers"], as_dict=True
			)
			or frappe._dict()
		)

		if self.packages:
			self.total_packages = sum(int(p.quantity or 0) for p in self.packages)
			pkg_weight = sum(flt(p.weight_kg) * int(p.quantity or 0) for p in self.packages)
			pkg_volume = sum(
				flt(p.length_cm) * flt(p.width_cm) * flt(p.height_cm) * int(p.quantity or 0) / 1e6
				for p in self.packages
			)
			# Typed totals win when the customer only knows the shipment-level figures.
			self.total_weight_kg = flt(pkg_weight, 2) or flt(self.total_weight_kg)
			self.total_volume_cbm = flt(pkg_volume, 3) or flt(self.total_volume_cbm)
		elif self.containers:
			self.total_packages = sum(int(c.quantity or 0) for c in self.containers)
			cw = sum(flt(c.weight_kg) * int(c.quantity or 0) for c in self.containers)
			self.total_weight_kg = flt(cw, 2) or flt(self.total_weight_kg)

		if mode.uses_containers and not self.containers:
			frappe.throw(_("Add at least one container for {0}.").format(self.transport_mode))
		if not mode.uses_containers and not (self.packages or flt(self.total_weight_kg)):
			frappe.throw(_("Add your packages, or at least the total weight."))

		divisor = VOLUMETRIC_KG_PER_CBM.get(mode.category)
		weight, volume = flt(self.total_weight_kg), flt(self.total_volume_cbm)
		if divisor:
			self.chargeable_weight_kg = flt(max(weight, volume * divisor), 2)
		else:
			# Sea LCL: W/M — 1 CBM or 1,000 kg, whichever is greater, expressed in kg.
			self.chargeable_weight_kg = flt(max(weight, volume * 1000), 2)

	def set_title(self):
		def place(city, country):
			return city or country or "?"

		mode = self.transport_mode or ""
		self.title = f"{place(self.origin_city, self.origin_country)} → {place(self.destination_city, self.destination_country)} · {mode}"

	def set_contact_defaults(self):
		if not self.customer:
			return
		c = frappe.db.get_value(
			"Sokan Customer", self.customer, ["full_name", "email", "phone", "company_name"], as_dict=True
		)
		if not c:
			return
		self.contact_name = self.contact_name or c.full_name
		self.contact_email = self.contact_email or c.email
		self.contact_phone = self.contact_phone or c.phone
		self.contact_company = self.contact_company or c.company_name

	def validate_route(self):
		if (
			self.origin_country == self.destination_country
			and (self.origin_city or "").strip().lower() == (self.destination_city or "").strip().lower()
		):
			frappe.throw(_("Origin and destination cannot be the same place."))

	def on_update(self):
		if self.status == "Open" and not self.published_on:
			self.db_set("published_on", now_datetime())
			from sokan.distribution import distribute

			distribute(self.name)

		if self.has_value_changed("status") and self.status in ("Cancelled", "Expired"):
			self.close_open_leads()

	def close_open_leads(self):
		from sokan.billing import refund

		refund_window = frappe.db.get_single_value("Sokan Settings", "refund_unlock_if_cancelled")
		recent = (
			self.status == "Cancelled"
			and self.published_on
			and time_diff_in_hours(now_datetime(), self.published_on) <= 24
			and not self.quote_count
		)
		for name in frappe.get_all(
			"Freight Request Lead",
			{"request": self.name, "status": ("in", ("New", "Unlocked"))},
			pluck="name",
		):
			lead = frappe.get_doc("Freight Request Lead", name)
			if refund_window and recent and lead.status == "Unlocked":
				refund(lead, _("Customer cancelled request {0}").format(self.name))
			lead.db_set("status", "Closed")
		frappe.db.set_value(
			"Freight Quote", {"request": self.name, "status": "Submitted"}, "status", "Expired"
		)

	def teu(self) -> int:
		return sum(
			CONTAINER_TEU.get((c.container_type or "")[:2], 1) * int(c.quantity or 0) for c in self.containers
		)
