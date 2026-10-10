import frappe
from frappe import _
from frappe.model.document import Document


class FreightRequestLead(Document):
	"""One request delivered to one forwarder — the unit Sokan bills on."""

	def validate(self):
		if self.is_new() and frappe.db.exists(
			"Freight Request Lead", {"request": self.request, "forwarder": self.forwarder}
		):
			frappe.throw(_("This request was already sent to {0}.").format(self.forwarder))


def on_doctype_update():
	frappe.db.add_unique(
		"Freight Request Lead", ["request", "forwarder"], constraint_name="unique_request_forwarder"
	)
	frappe.db.add_index("Freight Request Lead", ["forwarder", "status"])
