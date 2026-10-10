app_name = "sokan"
app_title = "Sokan"
app_publisher = "Alireza Emami"
app_description = "Sokan Leads"
app_email = "alireza@nisodynamic.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "sokan",
# 		"logo": "/assets/sokan/logo.png",
# 		"title": "Sokan",
# 		"route": "/sokan",
# 		"has_permission": "sokan.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/sokan/css/sokan.css"
# app_include_js = "/assets/sokan/js/sokan.js"

# include js, css files in header of web template
# web_include_css = "/assets/sokan/css/sokan.css"
# web_include_js = "/assets/sokan/js/sokan.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "sokan/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "sokan/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "sokan.utils.jinja_methods",
# 	"filters": "sokan.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "sokan.install.before_install"
after_install = "sokan.setup.install.after_install"
after_migrate = "sokan.setup.install.after_migrate"

# Uninstallation
# ------------

# before_uninstall = "sokan.uninstall.before_uninstall"
# after_uninstall = "sokan.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "sokan.utils.before_app_install"
# after_app_install = "sokan.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "sokan.utils.before_app_uninstall"
# after_app_uninstall = "sokan.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "sokan.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "sokan.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

scheduler_events = {
	"daily": [
		"sokan.tasks.expire_requests",
		"sokan.tasks.expire_quotes",
	],
	"monthly": [
		"sokan.tasks.charge_subscriptions",
	],
	# 08:00 server time: managers' summary of what's waiting.
	"cron": {
		"0 8 * * *": ["sokan.tasks.admin_digest"],
	},
}

# Portal users (customers / forwarders) live in the Nuxt app, not Frappe's /me.
role_home_page = {
	"Sokan Customer": "/account",
	"Sokan Forwarder": "/partner",
	"Sokan Admin": "/admin",
}

# ---------------

# scheduler_events = {
# 	"all": [
# 		"sokan.tasks.all"
# 	],
# 	"daily": [
# 		"sokan.tasks.daily"
# 	],
# 	"hourly": [
# 		"sokan.tasks.hourly"
# 	],
# 	"weekly": [
# 		"sokan.tasks.weekly"
# 	],
# 	"monthly": [
# 		"sokan.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "sokan.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "sokan.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "sokan.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "sokan.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["sokan.utils.before_request"]
# after_request = ["sokan.utils.after_request"]

# Job Events
# ----------
# before_job = ["sokan.utils.before_job"]
# after_job = ["sokan.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"sokan.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []
