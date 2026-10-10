"""Sign-ups now confirm their email with a code.

Everyone who signed up before this change keeps working as before: their
addresses are marked verified. The patch creates the field itself, because
post-model-sync patches run before after_migrate does.
"""

import frappe

from sokan.verification import FIELD, make_custom_fields


def execute():
	make_custom_fields()
	user = frappe.qb.DocType("User")
	frappe.qb.update(user).set(user[FIELD], 1).run()
