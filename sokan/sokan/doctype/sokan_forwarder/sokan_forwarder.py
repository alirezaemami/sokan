import frappe
from frappe import _
from frappe.model.document import Document

from sokan.utils import ROLE_FORWARDER, add_role, platform_currency, unique_slug


class SokanForwarder(Document):
	"""A freight forwarding company registered on Sokan."""

	def validate(self):
		if not self.slug:
			self.slug = unique_slug("Sokan Forwarder", self.company_name, self.name)
		else:
			self.slug = unique_slug("Sokan Forwarder", self.slug, self.name)
		if not self.plan:
			self.plan = frappe.db.get_value("Sokan Plan", {"is_default": 1, "is_active": 1}, "name")
		if not self.wallet_currency:
			self.wallet_currency = (
				frappe.db.get_value("Sokan Plan", self.plan, "currency") if self.plan else None
			) or platform_currency()
		self.validate_members()

	def validate_members(self):
		seen = set()
		for m in self.members:
			if m.user in seen:
				frappe.throw(_("{0} is listed twice in Members.").format(m.user))
			seen.add(m.user)
			other = frappe.db.get_value(
				"Sokan Forwarder Member",
				{"user": m.user, "parenttype": "Sokan Forwarder", "parent": ("!=", self.name or "")},
				"parent",
			)
			if other:
				frappe.throw(_("{0} already belongs to forwarder {1}.").format(m.user, other))

	def on_update(self):
		for m in self.members:
			add_role(m.user, ROLE_FORWARDER)

		if self.has_value_changed("status"):
			if self.status == "Active":
				from sokan.billing import grant_signup_bonus

				grant_signup_bonus(self)
			if self.status in ("Active", "Rejected", "Suspended") and not self.flags.in_insert:
				from sokan.notifications import notify_forwarder_status

				notify_forwarder_status(self)

	def after_insert(self):
		from sokan.notifications import notify_admin_new_forwarder

		notify_admin_new_forwarder(self)

	@property
	def mode_codes(self) -> list[str]:
		return [s.transport_mode for s in self.services]

	def owners(self) -> list[str]:
		return [m.user for m in self.members]
