"""Idempotent bootstrap: roles, transport modes, plans and settings defaults.

Runs after install and after every migrate, so a fresh site and an upgraded
one converge on the same reference data. Existing records are never
overwritten — admins are free to edit them in Desk.
"""

import frappe

from sokan.utils import ROLE_ADMIN, ROLE_CUSTOMER, ROLE_FORWARDER

ROLES = [
	# Managers work in the Nuxt admin portal; nobody needs Desk.
	(ROLE_ADMIN, 0),
	(ROLE_FORWARDER, 0),
	(ROLE_CUSTOMER, 0),
]

TRANSPORT_MODES = [
	# name, code, category, icon, uses_containers, description
	("Sea FCL", "sea_fcl", "Sea", "ship", 1, "Full container load — you book whole containers."),
	("Sea LCL", "sea_lcl", "Sea", "container", 0, "Less than container load — share space and pay per CBM."),
	("Air Freight", "air", "Air", "plane", 0, "Fastest for urgent and high-value cargo."),
	("Road FTL", "road_ftl", "Road", "truck", 0, "Full truck load, door to door."),
	("Road LTL", "road_ltl", "Road", "package", 0, "Groupage trucking for smaller loads."),
	("Rail Freight", "rail", "Rail", "train-front", 1, "Cost-efficient overland, e.g. China-Europe."),
	("Express Courier", "courier", "Courier", "zap", 0, "Parcels and documents, door to door."),
	("Project Cargo", "project", "Multimodal", "construction", 0, "Oversized, heavy-lift and breakbulk."),
]

PLANS = [
	{
		"plan_name": "Starter",
		"is_default": 1,
		"sort_order": 1,
		"monthly_fee": 0,
		"view_fee": 3,
		"quote_fee": 1,
		"free_views_per_month": 5,
		"free_quotes_per_month": 5,
		"description": "Pay only for the requests you open.",
		"features": [
			"All transport modes",
			"5 free unlocks every month",
			"Public company profile",
			"Email alerts",
		],
	},
	{
		"plan_name": "Growth",
		"badge": "Most popular",
		"sort_order": 2,
		"monthly_fee": 49,
		"view_fee": 1.5,
		"quote_fee": 0.5,
		"free_views_per_month": 40,
		"free_quotes_per_month": 40,
		"priority_listing": 1,
		"description": "For teams quoting every day.",
		"features": [
			"40 free unlocks / month",
			"Half-price fees after that",
			"Priority in quote lists",
			"Verified badge review",
		],
	},
	{
		"plan_name": "Enterprise",
		"sort_order": 3,
		"monthly_fee": 199,
		"view_fee": 0.5,
		"quote_fee": 0,
		"free_views_per_month": 250,
		"free_quotes_per_month": 1000,
		"priority_listing": 1,
		"description": "For networks and multi-branch forwarders.",
		"features": [
			"250 free unlocks / month",
			"Unlimited free quotes",
			"Featured on home page",
			"Dedicated account manager",
		],
	},
]


def after_install():
	setup()


def after_migrate():
	setup()


def setup():
	from sokan.verification import make_custom_fields

	make_custom_fields()
	make_roles()
	make_transport_modes()
	make_plans()
	set_settings_defaults()
	frappe.db.commit()


def make_roles():
	for role, desk_access in ROLES:
		if frappe.db.exists("Role", role):
			frappe.db.set_value("Role", role, "desk_access", desk_access, update_modified=False)
		else:
			frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": desk_access}).insert(
				ignore_permissions=True
			)


def make_transport_modes():
	for i, (name, code, category, icon, containers, description) in enumerate(TRANSPORT_MODES):
		if frappe.db.exists("Sokan Transport Mode", name):
			continue
		frappe.get_doc(
			{
				"doctype": "Sokan Transport Mode",
				"mode_name": name,
				"code": code,
				"category": category,
				"icon": icon,
				"uses_containers": containers,
				"description": description,
				"sort_order": i + 1,
			}
		).insert(ignore_permissions=True)


def make_plans():
	if frappe.db.count("Sokan Plan"):
		return
	for plan in PLANS:
		features = plan.pop("features")
		doc = frappe.get_doc({"doctype": "Sokan Plan", "currency": "USD", **plan})
		for f in features:
			doc.append("features", {"feature": f})
		doc.insert(ignore_permissions=True)


def set_settings_defaults():
	settings = frappe.get_single("Sokan Settings")
	if settings.default_currency:
		return
	for field in settings.meta.fields:
		if field.default and settings.get(field.fieldname) in (None, "", 0):
			settings.set(field.fieldname, field.default)
	settings.platform_name = settings.platform_name or "Sokan"
	settings.flags.ignore_mandatory = True
	settings.save(ignore_permissions=True)
