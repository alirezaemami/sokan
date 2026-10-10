import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class SokanReview(Document):
	"""A customer's rating of the forwarder they booked.

	Starts Pending; a manager approves it before it is public or counts
	toward the forwarder's rating.
	"""

	def validate(self):
		if not 1 <= int(self.rating or 0) <= 5:
			frappe.throw(_("Rating must be between 1 and 5."))
		self.status = self.status or "Pending"
		self.is_published = 1 if self.status == "Approved" else 0

	def on_update(self):
		refresh_rating(self.forwarder)

	def on_trash(self):
		refresh_rating(self.forwarder, exclude=self.name)


def refresh_rating(forwarder: str, exclude: str | None = None):
	filters = {"forwarder": forwarder, "is_published": 1}
	if exclude:
		filters["name"] = ("!=", exclude)
	rows = frappe.get_all("Sokan Review", filters=filters, pluck="rating")
	frappe.db.set_value(
		"Sokan Forwarder",
		forwarder,
		{"rating": flt(sum(rows) / len(rows), 2) if rows else 0, "review_count": len(rows)},
		update_modified=False,
	)
	# The home page caches forwarder cards (rating, latest review) for a short while.
	frappe.cache.delete_value("sokan:home")
