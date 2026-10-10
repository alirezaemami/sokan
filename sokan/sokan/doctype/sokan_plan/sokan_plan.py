import frappe
from frappe.model.document import Document


class SokanPlan(Document):
	"""A billing plan. Fees here override the platform defaults in Sokan Settings."""

	def on_update(self):
		# Exactly one default: new forwarders land on it and unpaid subscriptions fall back to it.
		if self.is_default:
			frappe.db.set_value(
				"Sokan Plan",
				{"is_default": 1, "name": ("!=", self.name)},
				"is_default",
				0,
				update_modified=False,
			)
