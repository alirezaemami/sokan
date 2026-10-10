from frappe.model.document import Document
from frappe.utils import flt


class FreightRequestPackage(Document):
	"""A group of identical packages. Volume is derived so a stale figure never survives a dimension edit."""

	def validate(self):
		self.volume_cbm = flt(
			flt(self.length_cm)
			* flt(self.width_cm)
			* flt(self.height_cm)
			* max(int(self.quantity or 0), 0)
			/ 1e6,
			3,
		)
