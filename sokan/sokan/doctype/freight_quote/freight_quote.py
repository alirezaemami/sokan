import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, nowdate


class FreightQuote(Document):
	"""A forwarder's price for a Freight Request."""

	def validate(self):
		if not self.charges:
			frappe.throw(_("Add at least one charge line."))
		total = 0.0
		for c in self.charges:
			c.currency = self.currency
			c.quantity = flt(c.quantity) or 1
			c.amount = flt(flt(c.quantity) * flt(c.unit_price), 2)
			if c.amount < 0:
				frappe.throw(_("Row {0}: charges cannot be negative.").format(c.idx))
			total += c.amount
		self.total_amount = flt(total, 2)
		if self.total_amount <= 0:
			frappe.throw(_("The quote total must be greater than zero."))

		if self.transit_days_min and self.transit_days_max and self.transit_days_min > self.transit_days_max:
			frappe.throw(_("Minimum transit time cannot exceed the maximum."))
		if self.is_new() and self.valid_until and getdate(self.valid_until) < getdate(nowdate()):
			frappe.throw(_("“Valid until” must be today or later."))


def on_doctype_update():
	frappe.db.add_index("Freight Quote", ["request", "status"])
