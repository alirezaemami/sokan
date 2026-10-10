"""bench commands for Sokan.

    bench --site sokan.local sokan-add-manager you@example.com --name "Your Name"

Creates the first manager (or grants the role to an existing user). Further
managers can be added from the admin portal's Settings → Managers.
"""

import click
from frappe.commands import get_site, pass_context


@click.command("sokan-add-manager")
@click.argument("email")
@click.option("--name", "full_name", default=None, help="Full name for a new account.")
@pass_context
def add_manager(context, email, full_name=None):
	"""Give EMAIL access to the Sokan admin portal (/admin)."""
	import frappe

	frappe.init(site=get_site(context))
	frappe.connect()
	try:
		frappe.set_user("Administrator")
		from sokan.api.admin import add_manager as grant

		grant(email, full_name)
		frappe.db.commit()
		click.echo(f"{email} can now sign in to /admin. New accounts get an email to set a password.")
	finally:
		frappe.destroy()


commands = [add_manager]
