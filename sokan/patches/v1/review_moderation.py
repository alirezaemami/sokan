"""Reviews now need a manager's approval before they are public.

None of the existing reviews were approved by anyone, so they all go to the
moderation queue, and forwarder ratings are recomputed without them.
"""

import frappe


def execute():
	frappe.db.sql("update `tabSokan Review` set status='Pending', is_published=0")

	from sokan.sokan.doctype.sokan_review.sokan_review import refresh_rating

	for forwarder in frappe.get_all("Sokan Review", distinct=True, pluck="forwarder"):
		refresh_rating(forwarder)
