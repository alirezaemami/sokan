from frappe.model.document import Document

from sokan.utils import ROLE_CUSTOMER, add_role


class SokanCustomer(Document):
	"""A shipper or importer who asks forwarders for prices."""

	def validate(self):
		if not self.email:
			self.email = self.user

	def on_update(self):
		add_role(self.user, ROLE_CUSTOMER)
