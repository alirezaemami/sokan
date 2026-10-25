"""Sokan's transactional email: one branded template, one message catalogue.

Every email Sokan sends is an entry in ``MESSAGES``, written in English and
Persian. ``send()`` renders it into ``templates/emails/sokan_notification.html``
once per language, in each recipient's own language (User.language, set from
the site language they signed up in).

Placeholders use ``{name}`` syntax. Values are escaped before they are put into
the HTML, so user-supplied text (company names, comments, reasons) can never
inject markup; only the catalogue's own ``<b>`` tags survive.

Sending is fire-and-forget: a mail failure is logged and never rolls back the
business action that triggered it, and no request ever waits on the mail server.
"""

from urllib.parse import urlparse

import frappe
from frappe.utils import escape_html

from sokan.utils import frontend_url, get_settings

# --------------------------------------------------------------------------- catalogue
# audience → which footer line explains why the recipient got the email.
# body items: a string, or {"if": "<ctx key>", "text": "..."} included only when that key is truthy.

MESSAGES: dict[str, dict] = {
	# ----------------------------------------------------------------- account
	"welcome_shipper": {
		"audience": "account",
		"en": {
			"subject": "Welcome to Sokan",
			"eyebrow": "Your account",
			"heading": "Welcome aboard, {first_name}",
			"body": [
				"Your Sokan account is ready. Describe a shipment once and every matching, verified forwarder sends you an all-in price.",
				"It's free for shippers, always. You only compare and book.",
			],
			"cta": "Post your first request",
		},
		"fa": {
			"subject": "به سکان خوش آمدید",
			"eyebrow": "حساب کاربری",
			"heading": "{first_name}، خوش آمدید",
			"body": [
				"حساب سکان شما آماده است. یک بار محموله‌تان را شرح دهید تا همه فورواردرهای تأییدشده و مرتبط، قیمت کامل برایتان بفرستند.",
				"استفاده از سکان برای صاحبان کالا همیشه رایگان است. شما فقط مقایسه و رزرو می‌کنید.",
			],
			"cta": "ثبت اولین درخواست",
		},
	},
	"welcome_forwarder": {
		"audience": "account",
		"en": {
			"subject": "We received your application",
			"eyebrow": "Application received",
			"heading": "Thanks for joining Sokan",
			"body": [
				"<b>{company}</b> is now in our review queue. We check every company before it can quote, usually within one business day.",
				"We'll email you the moment you're approved. Meanwhile, completing your company profile helps shippers choose you.",
			],
			"cta": "Complete your profile",
		},
		"fa": {
			"subject": "درخواست عضویت شما دریافت شد",
			"eyebrow": "درخواست عضویت",
			"heading": "از پیوستن شما به سکان سپاسگزاریم",
			"body": [
				"<b>{company}</b> در صف بررسی ماست. هر شرکت پیش از ارسال قیمت بررسی می‌شود؛ معمولاً ظرف یک روز کاری.",
				"به محض تأیید به شما ایمیل می‌زنیم. تا آن زمان، تکمیل پروفایل شرکت به صاحبان کالا کمک می‌کند شما را انتخاب کنند.",
			],
			"cta": "تکمیل پروفایل",
		},
	},
	"verify_code": {
		"audience": "security",
		"en": {
			"subject": "{code} is your Sokan verification code",
			"eyebrow": "Confirm your email",
			"heading": "Your verification code",
			"body": [
				"Enter this code on Sokan to confirm that <b>{email}</b> is your address.",
				"It expires in {minutes} minutes.",
			],
			"note": "Didn't sign up for Sokan? Someone may have typed your address by mistake. Ignore this email and the account won't be activated.",
		},
		"fa": {
			"subject": "کد تأیید سکان شما: {code}",
			"eyebrow": "تأیید ایمیل",
			"heading": "کد تأیید شما",
			"body": [
				"این کد را در سکان وارد کنید تا تأیید شود <b>{email}</b> متعلق به شماست.",
				"این کد تا {minutes} دقیقه معتبر است.",
			],
			"note": "در سکان ثبت‌نام نکرده‌اید؟ ممکن است کسی نشانی شما را اشتباه وارد کرده باشد. این ایمیل را نادیده بگیرید؛ حساب فعال نمی‌شود.",
		},
	},
	"password_reset": {
		"audience": "security",
		"en": {
			"subject": "Reset your Sokan password",
			"eyebrow": "Security",
			"heading": "Reset your password",
			"body": [
				"We received a request to reset the password for <b>{email}</b>.",
				"The link below works once and expires in {minutes} minutes.",
			],
			"cta": "Choose a new password",
			"note": "Didn't ask for this? You can ignore this email; your password stays the same.",
		},
		"fa": {
			"subject": "بازنشانی رمز عبور سکان",
			"eyebrow": "امنیت",
			"heading": "بازنشانی رمز عبور",
			"body": [
				"درخواستی برای بازنشانی رمز عبور <b>{email}</b> دریافت کردیم.",
				"پیوند زیر فقط یک بار کار می‌کند و تا {minutes} دقیقه معتبر است.",
			],
			"cta": "انتخاب رمز عبور جدید",
			"note": "این درخواست از طرف شما نبوده؟ این ایمیل را نادیده بگیرید؛ رمز عبورتان تغییری نمی‌کند.",
		},
	},
	"password_changed": {
		"audience": "security",
		"en": {
			"subject": "Your Sokan password was changed",
			"eyebrow": "Security",
			"heading": "Your password was changed",
			"body": [
				"The password for <b>{email}</b> was just changed, and you were signed out on other devices.",
				"If this wasn't you, reset your password straight away and let us know.",
			],
			"cta": "Reset password",
		},
		"fa": {
			"subject": "رمز عبور سکان شما تغییر کرد",
			"eyebrow": "امنیت",
			"heading": "رمز عبور شما تغییر کرد",
			"body": [
				"رمز عبور <b>{email}</b> همین حالا تغییر کرد و از دستگاه‌های دیگر خارج شدید.",
				"اگر این کار شما نبوده، فوراً رمز عبور را بازنشانی کنید و به ما اطلاع دهید.",
			],
			"cta": "بازنشانی رمز عبور",
		},
	},
	"manager_invite": {
		"audience": "manager",
		"en": {
			"subject": "You're now a Sokan manager",
			"eyebrow": "Management access",
			"heading": "Welcome to the Sokan team",
			"body": [
				"{inviter} gave <b>{email}</b> access to Sokan management: approvals, payments, reviews, reports and settings.",
				{"if": "new_account", "text": "Your account is new, so start by choosing a password."},
				{
					"if": "existing_account",
					"text": "Sign in with your usual password; you'll land in the management area.",
				},
			],
			"cta": "{cta_label}",
		},
		"fa": {
			"subject": "شما اکنون مدیر سکان هستید",
			"eyebrow": "دسترسی مدیریت",
			"heading": "به تیم سکان خوش آمدید",
			"body": [
				"{inviter} به <b>{email}</b> دسترسی مدیریت سکان داد: تأییدها، پرداخت‌ها، نظرات، گزارش‌ها و تنظیمات.",
				{"if": "new_account", "text": "حساب شما تازه ساخته شده؛ ابتدا یک رمز عبور انتخاب کنید."},
				{
					"if": "existing_account",
					"text": "با رمز عبور همیشگی وارد شوید؛ مستقیم به بخش مدیریت می‌روید.",
				},
			],
			"cta": "{cta_label}",
		},
	},
	# ----------------------------------------------------------------- shippers
	"request_published": {
		"audience": "shipper",
		"en": {
			"subject": "Your request is live: {title}",
			"eyebrow": "Request {request}",
			"heading": "Forwarders are on it",
			"body": [
				{
					"if": "count",
					"text": "We sent your request to <b>{count} matching forwarders</b>. You'll get an email as each quote arrives.",
				},
				{
					"if": "none",
					"text": "No forwarder covers this lane and mode yet. Your request stays open, and companies that join before it closes will see it.",
				},
			],
			"cta": "View your request",
		},
		"fa": {
			"subject": "درخواست شما منتشر شد: {title}",
			"eyebrow": "درخواست {request}",
			"heading": "فورواردرها در جریان هستند",
			"body": [
				{
					"if": "count",
					"text": "درخواست شما برای <b>{count} فورواردر مرتبط</b> ارسال شد. با رسیدن هر قیمت ایمیل دریافت می‌کنید.",
				},
				{
					"if": "none",
					"text": "هنوز فورواردری این مسیر و روش حمل را پوشش نمی‌دهد. درخواست شما باز می‌ماند و شرکت‌هایی که تا پایان مهلت بپیوندند آن را می‌بینند.",
				},
			],
			"cta": "مشاهده درخواست",
		},
	},
	"new_quote": {
		"audience": "shipper",
		"en": {
			"subject": "New quote for {title}: {amount}",
			"eyebrow": "Request {request}",
			"heading": "You have a new quote",
			"body": [
				"<b>{forwarder}</b> quoted <b>{amount}</b> all-in for {title}.",
				"You now have {count} quote(s) to compare side by side.",
			],
			"cta": "Compare quotes",
		},
		"fa": {
			"subject": "قیمت جدید برای {title}: {amount}",
			"eyebrow": "درخواست {request}",
			"heading": "یک قیمت جدید دارید",
			"body": [
				"<b>{forwarder}</b> برای {title} قیمت کامل <b>{amount}</b> ارسال کرد.",
				"اکنون {count} قیمت برای مقایسه دارید.",
			],
			"cta": "مقایسه قیمت‌ها",
		},
	},
	"quote_updated": {
		"audience": "shipper",
		"en": {
			"subject": "{forwarder} updated their quote: {amount}",
			"eyebrow": "Request {request}",
			"heading": "A quote was revised",
			"body": ["<b>{forwarder}</b> revised their quote for {title}. The new total is <b>{amount}</b>."],
			"cta": "Compare quotes",
		},
		"fa": {
			"subject": "{forwarder} قیمت خود را به‌روز کرد: {amount}",
			"eyebrow": "درخواست {request}",
			"heading": "یک قیمت ویرایش شد",
			"body": [
				"<b>{forwarder}</b> قیمت خود برای {title} را ویرایش کرد. مبلغ جدید <b>{amount}</b> است."
			],
			"cta": "مقایسه قیمت‌ها",
		},
	},
	"booking_confirmed": {
		"audience": "shipper",
		"en": {
			"subject": "Booked: {title} with {forwarder}",
			"eyebrow": "Booking confirmed",
			"heading": "Your shipment is booked",
			"body": [
				"You accepted <b>{forwarder}</b>'s quote of <b>{amount}</b>. They now have your contact details and will reach out to arrange collection and documents.",
				"Here's how to reach them directly:",
			],
			"cta": "View booking",
			"note": "Once the shipment is done, a short review helps other shippers choose.",
		},
		"fa": {
			"subject": "رزرو شد: {title} با {forwarder}",
			"eyebrow": "تأیید رزرو",
			"heading": "محموله شما رزرو شد",
			"body": [
				"قیمت <b>{amount}</b> از <b>{forwarder}</b> را پذیرفتید. آن‌ها اکنون اطلاعات تماس شما را دارند و برای هماهنگی بارگیری و اسناد با شما تماس می‌گیرند.",
				"راه‌های تماس مستقیم با آن‌ها:",
			],
			"cta": "مشاهده رزرو",
			"note": "پس از انجام حمل، ثبت یک نظر کوتاه به دیگر صاحبان کالا در انتخاب کمک می‌کند.",
		},
	},
	"request_expired": {
		"audience": "shipper",
		"en": {
			"subject": "Your request has closed: {title}",
			"eyebrow": "Request {request}",
			"heading": "The quoting window has ended",
			"body": [
				{
					"if": "count",
					"text": "{title} closed with <b>{count} quote(s)</b>. You can still review them, or post the shipment again with new dates.",
				},
				{
					"if": "none",
					"text": "{title} closed without quotes. Widening the dates or adding cargo details often helps; new forwarders join every week.",
				},
			],
			"cta": "Post a new request",
		},
		"fa": {
			"subject": "مهلت درخواست شما تمام شد: {title}",
			"eyebrow": "درخواست {request}",
			"heading": "مهلت دریافت قیمت به پایان رسید",
			"body": [
				{
					"if": "count",
					"text": "{title} با <b>{count} قیمت</b> بسته شد. همچنان می‌توانید آن‌ها را ببینید یا محموله را با تاریخ‌های جدید دوباره ثبت کنید.",
				},
				{
					"if": "none",
					"text": "{title} بدون قیمت بسته شد. گسترده‌تر کردن تاریخ‌ها یا افزودن جزئیات بار معمولاً کمک می‌کند؛ هر هفته فورواردرهای جدیدی می‌پیوندند.",
				},
			],
			"cta": "ثبت درخواست جدید",
		},
	},
	"request_cancelled_by_admin": {
		"audience": "shipper",
		"en": {
			"subject": "Your request {request} was cancelled",
			"eyebrow": "Request {request}",
			"heading": "We cancelled your request",
			"body": [
				"The Sokan team cancelled <b>{title}</b>.",
				"Reason: {reason}",
				"Reply to this email if you have any questions.",
			],
			"cta": "Open your requests",
		},
		"fa": {
			"subject": "درخواست {request} شما لغو شد",
			"eyebrow": "درخواست {request}",
			"heading": "درخواست شما لغو شد",
			"body": [
				"تیم سکان <b>{title}</b> را لغو کرد.",
				"دلیل: {reason}",
				"اگر پرسشی دارید به همین ایمیل پاسخ دهید.",
			],
			"cta": "مشاهده درخواست‌ها",
		},
	},
	"review_published": {
		"audience": "shipper",
		"en": {
			"subject": "Your review of {forwarder} is live",
			"eyebrow": "Thank you",
			"heading": "Your review is published",
			"body": [
				"Your review of <b>{forwarder}</b> is now on their public profile, helping other shippers choose with confidence."
			],
			"cta": "See it on their profile",
		},
		"fa": {
			"subject": "نظر شما درباره {forwarder} منتشر شد",
			"eyebrow": "سپاسگزاریم",
			"heading": "نظر شما منتشر شد",
			"body": [
				"نظر شما درباره <b>{forwarder}</b> اکنون روی پروفایل عمومی آن‌ها نمایش داده می‌شود و به دیگر صاحبان کالا کمک می‌کند."
			],
			"cta": "مشاهده در پروفایل",
		},
	},
	# ----------------------------------------------------------------- forwarders
	"forwarder_approved": {
		"audience": "forwarder",
		"en": {
			"subject": "{company} is live on Sokan",
			"eyebrow": "Approved",
			"heading": "You're approved. Welcome!",
			"body": [
				"<b>{company}</b> is now listed on Sokan and will receive freight requests that match your services and lanes.",
				{"if": "bonus", "text": "We've added <b>{bonus}</b> welcome credit to your wallet."},
				{
					"if": "open_leads",
					"text": "{open_leads} open request(s) are already waiting in your inbox.",
				},
			],
			"cta": "Open partner portal",
		},
		"fa": {
			"subject": "{company} در سکان فعال شد",
			"eyebrow": "تأیید شد",
			"heading": "تأیید شدید. خوش آمدید!",
			"body": [
				"<b>{company}</b> اکنون در سکان فهرست شده و درخواست‌های حمل منطبق با خدمات و مسیرهای شما را دریافت می‌کند.",
				{"if": "bonus", "text": "<b>{bonus}</b> اعتبار خوش‌آمد به کیف پول شما اضافه شد."},
				{"if": "open_leads", "text": "{open_leads} درخواست باز هم‌اکنون در صندوق شما منتظر است."},
			],
			"cta": "ورود به پنل همکاران",
		},
	},
	"forwarder_rejected": {
		"audience": "forwarder",
		"en": {
			"subject": "About your Sokan application",
			"eyebrow": "Application",
			"heading": "We couldn't approve {company} yet",
			"body": [
				"Reason: {reason}",
				"Once this is fixed, update your profile and reply to this email; we'll review it again.",
			],
			"cta": "Update your profile",
		},
		"fa": {
			"subject": "درباره درخواست عضویت شما در سکان",
			"eyebrow": "درخواست عضویت",
			"heading": "فعلاً امکان تأیید {company} نبود",
			"body": [
				"دلیل: {reason}",
				"پس از رفع مشکل، پروفایل را به‌روز کنید و به همین ایمیل پاسخ دهید تا دوباره بررسی کنیم.",
			],
			"cta": "به‌روزرسانی پروفایل",
		},
	},
	"forwarder_suspended": {
		"audience": "forwarder",
		"en": {
			"subject": "Your Sokan account is suspended",
			"eyebrow": "Account",
			"heading": "{company} is suspended",
			"body": [
				"You won't receive new requests, and unlocking and quoting are paused.",
				"Reason: {reason}",
				"Reply to this email to resolve it.",
			],
			"cta": "Open partner portal",
		},
		"fa": {
			"subject": "حساب سکان شما معلق شد",
			"eyebrow": "حساب کاربری",
			"heading": "{company} معلق شد",
			"body": [
				"درخواست جدیدی دریافت نمی‌کنید و باز کردن درخواست و ارسال قیمت متوقف است.",
				"دلیل: {reason}",
				"برای رفع آن به همین ایمیل پاسخ دهید.",
			],
			"cta": "ورود به پنل همکاران",
		},
	},
	"new_lead": {
		"audience": "forwarder_leads",
		"en": {
			"subject": "New request: {title}",
			"eyebrow": "New lead",
			"heading": "A shipment needs a price",
			"body": [
				"A shipper on your lanes is collecting quotes. The summary is free to view; unlock it for the full details and to send your price."
			],
			"cta": "View request",
		},
		"fa": {
			"subject": "درخواست جدید: {title}",
			"eyebrow": "سرنخ جدید",
			"heading": "یک محموله منتظر قیمت است",
			"body": [
				"یک صاحب کالا در مسیرهای شما در حال دریافت قیمت است. خلاصه رایگان است؛ برای جزئیات کامل و ارسال قیمت آن را باز کنید."
			],
			"cta": "مشاهده درخواست",
		},
	},
	"quote_won": {
		"audience": "forwarder",
		"en": {
			"subject": "You won it: {title}",
			"eyebrow": "Quote accepted",
			"heading": "Your quote was accepted",
			"body": [
				"The shipper accepted your quote of <b>{amount}</b> for {title}. Get in touch to arrange the shipment:"
			],
			"cta": "Open booking",
		},
		"fa": {
			"subject": "برنده شدید: {title}",
			"eyebrow": "قیمت پذیرفته شد",
			"heading": "قیمت شما پذیرفته شد",
			"body": [
				"صاحب کالا قیمت <b>{amount}</b> شما برای {title} را پذیرفت. برای هماهنگی حمل تماس بگیرید:"
			],
			"cta": "مشاهده رزرو",
		},
	},
	"quote_lost": {
		"audience": "forwarder_quotes",
		"en": {
			"subject": "Update on {title}",
			"eyebrow": "Quote {quote}",
			"heading": "The shipper chose another offer",
			"body": [
				"Thanks for quoting <b>{amount}</b> for {title}. The shipper went with a different offer this time.",
				{"if": "reason", "text": "Their note: {reason}"},
			],
			"cta": "See new requests",
		},
		"fa": {
			"subject": "به‌روزرسانی درباره {title}",
			"eyebrow": "قیمت {quote}",
			"heading": "صاحب کالا پیشنهاد دیگری را انتخاب کرد",
			"body": [
				"از ارسال قیمت <b>{amount}</b> برای {title} سپاسگزاریم. این بار صاحب کالا پیشنهاد دیگری را انتخاب کرد.",
				{"if": "reason", "text": "یادداشت صاحب کالا: {reason}"},
			],
			"cta": "مشاهده درخواست‌های جدید",
		},
	},
	"lead_cancelled": {
		"audience": "forwarder",
		"en": {
			"subject": "Request cancelled: {title}",
			"eyebrow": "Request {request}",
			"heading": "This request was cancelled",
			"body": [
				"The shipper cancelled {title}, so it no longer accepts quotes.",
				{"if": "refund", "text": "We refunded your unlock fee of <b>{refund}</b> to your wallet."},
			],
			"cta": "See other requests",
		},
		"fa": {
			"subject": "درخواست لغو شد: {title}",
			"eyebrow": "درخواست {request}",
			"heading": "این درخواست لغو شد",
			"body": [
				"صاحب کالا {title} را لغو کرد و دیگر قیمتی نمی‌پذیرد.",
				{"if": "refund", "text": "کارمزد باز کردن به مبلغ <b>{refund}</b> به کیف پول شما برگشت."},
			],
			"cta": "مشاهده درخواست‌های دیگر",
		},
	},
	"topup_received": {
		"audience": "forwarder",
		"en": {
			"subject": "Top-up {topup} received",
			"eyebrow": "Wallet",
			"heading": "We received your top-up request",
			"body": [
				"We'll credit <b>{amount}</b> to your wallet as soon as our team confirms the payment, usually within one business day."
			],
			"cta": "Open wallet",
		},
		"fa": {
			"subject": "درخواست شارژ {topup} دریافت شد",
			"eyebrow": "کیف پول",
			"heading": "درخواست شارژ شما دریافت شد",
			"body": [
				"به محض تأیید پرداخت توسط تیم ما، <b>{amount}</b> به کیف پول شما اضافه می‌شود؛ معمولاً ظرف یک روز کاری."
			],
			"cta": "مشاهده کیف پول",
		},
	},
	"topup_approved": {
		"audience": "forwarder",
		"en": {
			"subject": "{amount} added to your Sokan wallet",
			"eyebrow": "Wallet",
			"heading": "Your top-up is in",
			"body": ["Top-up {topup} was approved and <b>{amount}</b> is now in your wallet."],
			"cta": "Open wallet",
		},
		"fa": {
			"subject": "{amount} به کیف پول سکان شما اضافه شد",
			"eyebrow": "کیف پول",
			"heading": "شارژ انجام شد",
			"body": ["شارژ {topup} تأیید شد و <b>{amount}</b> به کیف پول شما اضافه شد."],
			"cta": "مشاهده کیف پول",
		},
	},
	"topup_rejected": {
		"audience": "forwarder",
		"en": {
			"subject": "Top-up {topup} could not be approved",
			"eyebrow": "Wallet",
			"heading": "We couldn't confirm your top-up",
			"body": [
				"Your top-up of <b>{amount}</b> was not approved.",
				"Reason: {reason}",
				"Reply to this email if you think this is a mistake.",
			],
			"cta": "Open wallet",
		},
		"fa": {
			"subject": "شارژ {topup} تأیید نشد",
			"eyebrow": "کیف پول",
			"heading": "امکان تأیید شارژ نبود",
			"body": [
				"شارژ <b>{amount}</b> شما تأیید نشد.",
				"دلیل: {reason}",
				"اگر فکر می‌کنید اشتباهی رخ داده، به همین ایمیل پاسخ دهید.",
			],
			"cta": "مشاهده کیف پول",
		},
	},
	"low_balance": {
		"audience": "forwarder",
		"en": {
			"subject": "Your Sokan wallet is running low",
			"eyebrow": "Wallet",
			"heading": "Top up to keep quoting",
			"body": [
				"Your wallet balance is <b>{balance}</b>, below your {threshold} warning level.",
				"Once your free monthly allowance is used, unlocking a request costs {view_fee} and sending a quote {quote_fee}.",
			],
			"cta": "Top up now",
		},
		"fa": {
			"subject": "موجودی کیف پول سکان شما رو به اتمام است",
			"eyebrow": "کیف پول",
			"heading": "برای ادامه ارسال قیمت، شارژ کنید",
			"body": [
				"موجودی کیف پول شما <b>{balance}</b> است؛ کمتر از سطح هشدار {threshold}.",
				"پس از اتمام سهمیه رایگان ماهانه، باز کردن هر درخواست {view_fee} و ارسال هر قیمت {quote_fee} هزینه دارد.",
			],
			"cta": "شارژ کیف پول",
		},
	},
	"wallet_adjusted": {
		"audience": "forwarder",
		"en": {
			"subject": "Your Sokan wallet was adjusted",
			"eyebrow": "Wallet",
			"heading": "Balance adjustment",
			"body": [
				"The Sokan team posted an adjustment of <b>{amount}</b> to your wallet.",
				"Note: {note}",
			],
			"cta": "Open wallet",
		},
		"fa": {
			"subject": "موجودی کیف پول سکان شما اصلاح شد",
			"eyebrow": "کیف پول",
			"heading": "اصلاح موجودی",
			"body": ["تیم سکان اصلاحی به مبلغ <b>{amount}</b> در کیف پول شما ثبت کرد.", "توضیح: {note}"],
			"cta": "مشاهده کیف پول",
		},
	},
	"plan_renewed": {
		"audience": "forwarder",
		"en": {
			"subject": "Your {plan} plan renewed",
			"eyebrow": "Plan",
			"heading": "{plan} plan renewed",
			"body": [
				"We charged <b>{fee}</b> for your {plan} plan for {month}. Your free monthly allowance has been reset."
			],
			"cta": "Open wallet",
		},
		"fa": {
			"subject": "طرح {plan} شما تمدید شد",
			"eyebrow": "طرح",
			"heading": "طرح {plan} تمدید شد",
			"body": [
				"مبلغ <b>{fee}</b> بابت طرح {plan} برای {month} کسر شد. سهمیه رایگان ماهانه شما از نو شروع شد."
			],
			"cta": "مشاهده کیف پول",
		},
	},
	"plan_downgraded": {
		"audience": "forwarder",
		"en": {
			"subject": "Your plan changed to {plan}",
			"eyebrow": "Plan",
			"heading": "We moved you to the {plan} plan",
			"body": [
				"We couldn't charge <b>{fee}</b> for your {old_plan} plan because your wallet balance was too low, so {company} moved to the {plan} plan.",
				"Top up and switch back any time from your wallet.",
			],
			"cta": "Top up and switch back",
		},
		"fa": {
			"subject": "طرح شما به {plan} تغییر کرد",
			"eyebrow": "طرح",
			"heading": "طرح شما به {plan} تغییر کرد",
			"body": [
				"به دلیل کافی نبودن موجودی، امکان کسر <b>{fee}</b> برای طرح {old_plan} نبود و {company} به طرح {plan} منتقل شد.",
				"هر زمان بخواهید می‌توانید کیف پول را شارژ کنید و از همان‌جا به طرح قبلی برگردید.",
			],
			"cta": "شارژ و بازگشت به طرح",
		},
	},
	"new_review": {
		"audience": "forwarder_quotes",
		"en": {
			"subject": "New {rating}★ review for {company}",
			"eyebrow": "Review",
			"heading": "A shipper reviewed you",
			"body": ["{author} rated <b>{company}</b> {stars}", {"if": "comment", "text": "“{comment}”"}],
			"cta": "See your profile",
		},
		"fa": {
			"subject": "نظر جدید {rating} ستاره برای {company}",
			"eyebrow": "نظر",
			"heading": "یک صاحب کالا به شما امتیاز داد",
			"body": [
				"{author} به <b>{company}</b> امتیاز {stars} داد",
				{"if": "comment", "text": "«{comment}»"},
			],
			"cta": "مشاهده پروفایل",
		},
	},
	# ----------------------------------------------------------------- managers
	"admin_new_forwarder": {
		"audience": "manager",
		"en": {
			"subject": "New forwarder to approve: {company}",
			"eyebrow": "Approval needed",
			"heading": "A forwarder signed up",
			"body": ["<b>{company}</b> registered and is waiting for approval."],
			"cta": "Review company",
		},
		"fa": {
			"subject": "فورواردر جدید برای تأیید: {company}",
			"eyebrow": "نیاز به تأیید",
			"heading": "یک فورواردر ثبت‌نام کرد",
			"body": ["<b>{company}</b> ثبت‌نام کرده و منتظر تأیید است."],
			"cta": "بررسی شرکت",
		},
	},
	"admin_new_topup": {
		"audience": "manager",
		"en": {
			"subject": "Top-up to check: {amount} from {company}",
			"eyebrow": "Payment to confirm",
			"heading": "A forwarder requested a top-up",
			"body": ["Check the payment arrived, then approve it to credit the wallet."],
			"cta": "Review top-ups",
		},
		"fa": {
			"subject": "شارژ برای بررسی: {amount} از {company}",
			"eyebrow": "پرداخت برای تأیید",
			"heading": "یک فورواردر درخواست شارژ داد",
			"body": ["پس از اطمینان از رسیدن وجه، آن را تأیید کنید تا کیف پول شارژ شود."],
			"cta": "بررسی شارژها",
		},
	},
	"admin_new_review": {
		"audience": "manager",
		"en": {
			"subject": "Review to moderate: {rating}★ for {company}",
			"eyebrow": "Moderation",
			"heading": "A new review is waiting",
			"body": [
				"{author} rated <b>{company}</b> {stars}",
				{"if": "comment", "text": "“{comment}”"},
				"It stays hidden until you publish it.",
			],
			"cta": "Moderate reviews",
		},
		"fa": {
			"subject": "نظر برای بررسی: {rating} ستاره برای {company}",
			"eyebrow": "بررسی",
			"heading": "یک نظر جدید منتظر است",
			"body": [
				"{author} به <b>{company}</b> امتیاز {stars} داد",
				{"if": "comment", "text": "«{comment}»"},
				"تا زمانی که منتشرش نکنید پنهان می‌ماند.",
			],
			"cta": "بررسی نظرات",
		},
	},
	"admin_new_message": {
		"audience": "manager",
		"en": {
			"subject": "New message: {subject_line}",
			"eyebrow": "Contact form",
			"heading": "{name} sent a message",
			"body": ["{message}"],
			"cta": "Open messages",
		},
		"fa": {
			"subject": "پیام جدید: {subject_line}",
			"eyebrow": "فرم تماس",
			"heading": "{name} پیامی فرستاد",
			"body": ["{message}"],
			"cta": "مشاهده پیام‌ها",
		},
	},
	"admin_digest": {
		"audience": "manager",
		"en": {
			"subject": "Sokan today: {total} item(s) waiting",
			"eyebrow": "Daily summary",
			"heading": "Here's what's waiting for you",
			"body": ["Yesterday: {requests} new request(s), {quotes} quote(s) and {bookings} booking(s)."],
			"cta": "Open management",
		},
		"fa": {
			"subject": "سکان امروز: {total} مورد منتظر شماست",
			"eyebrow": "خلاصه روزانه",
			"heading": "کارهایی که منتظر شماست",
			"body": ["دیروز: {requests} درخواست جدید، {quotes} قیمت و {bookings} رزرو."],
			"cta": "ورود به بخش مدیریت",
		},
	},
}

# Fact-table labels, by key.
LABELS = {
	"request": ("Request", "درخواست"),
	"route": ("Route", "مسیر"),
	"mode": ("Mode", "روش حمل"),
	"commodity": ("Commodity", "کالا"),
	"ready": ("Cargo ready", "آمادگی بار"),
	"valid_until": ("Accepting quotes until", "دریافت قیمت تا"),
	"forwarder": ("Forwarder", "فورواردر"),
	"total": ("Total", "مبلغ کل"),
	"transit": ("Transit time", "زمان ترانزیت"),
	"quote_valid": ("Quote valid until", "اعتبار قیمت تا"),
	"email": ("Email", "ایمیل"),
	"phone": ("Phone", "تلفن"),
	"website": ("Website", "وب‌سایت"),
	"contact": ("Contact", "شخص تماس"),
	"company": ("Company", "شرکت"),
	"amount": ("Amount", "مبلغ"),
	"method": ("Payment method", "روش پرداخت"),
	"reference": ("Reference", "شماره پیگیری"),
	"balance": ("New balance", "موجودی جدید"),
	"country": ("Country", "کشور"),
	"plan": ("Plan", "طرح"),
	"companies": ("Companies to approve", "شرکت برای تأیید"),
	"topups": ("Top-ups to check", "شارژ برای بررسی"),
	"reviews": ("Reviews to moderate", "نظر برای بررسی"),
	"messages": ("New messages", "پیام جدید"),
}

COMMON = {
	"en": {
		"signoff": "The Sokan team",
		"link_hint": "Button not working? Paste this link into your browser:",
		"prefs": "Email preferences",
		"reason": {
			"account": "You're receiving this because you created a Sokan account.",
			"security": "We send security emails to keep your account safe.",
			"shipper": "You're receiving this about a shipment you posted on Sokan.",
			"forwarder": "You're receiving this as a member of a forwarder on Sokan.",
			"forwarder_leads": "You're receiving new-request alerts for your company on Sokan.",
			"forwarder_quotes": "You're receiving quote updates for your company on Sokan.",
			"manager": "You're receiving this as a Sokan manager.",
		},
		"days": "{min}–{max} days",
	},
	"fa": {
		"signoff": "تیم سکان",
		"link_hint": "دکمه کار نمی‌کند؟ این پیوند را در مرورگر باز کنید:",
		"prefs": "تنظیمات ایمیل",
		"reason": {
			"account": "این ایمیل را دریافت می‌کنید چون در سکان حساب کاربری ساخته‌اید.",
			"security": "ایمیل‌های امنیتی را برای حفاظت از حساب شما می‌فرستیم.",
			"shipper": "این ایمیل درباره محموله‌ای است که در سکان ثبت کرده‌اید.",
			"forwarder": "این ایمیل را به عنوان عضو یک شرکت فورواردر در سکان دریافت می‌کنید.",
			"forwarder_leads": "هشدار درخواست‌های جدید شرکت شما در سکان فعال است.",
			"forwarder_quotes": "اطلاع‌رسانی قیمت‌های شرکت شما در سکان فعال است.",
			"manager": "این ایمیل را به عنوان مدیر سکان دریافت می‌کنید.",
		},
		"days": "{min} تا {max} روز",
	},
}

LANGS = ("en", "fa")


# --------------------------------------------------------------------------- rendering


class _Escaped(dict):
	"""format_map source: escapes every value, and leaves unknown placeholders blank."""

	def __missing__(self, key):
		return ""


def _fill(text: str, ctx: dict, escape: bool = True) -> str:
	"""Fill placeholders. In HTML, each value is escaped and isolated with <bdi>, so a
	Latin amount or ID keeps its own direction inside a Persian sentence (and vice versa)."""
	if escape:
		values = _Escaped({k: f"<bdi>{escape_html(str(v))}</bdi>" for k, v in ctx.items() if v is not None})
	else:
		values = _Escaped({k: str(v) for k, v in ctx.items() if v is not None})
	return text.format_map(values)


def label(key: str, lang: str) -> str:
	en, fa = LABELS.get(key, (key, key))
	return fa if lang == "fa" else en


def days(min_days, max_days, lang: str) -> str | None:
	if not (min_days or max_days):
		return None
	return COMMON[lang]["days"].format(min=min_days or max_days, max=max_days or min_days)


def render(
	event: str, lang: str, ctx: dict, facts=None, path: str | None = None, prefs: bool = False
) -> tuple[str, str]:
	"""Return (subject, html) for one event in one language."""
	spec = MESSAGES[event]
	m = spec[lang if lang in LANGS else "en"]
	common = COMMON[lang if lang in LANGS else "en"]
	settings = get_settings()
	site = frontend_url()
	rtl = lang == "fa"

	body = []
	for item in m["body"]:
		if isinstance(item, dict):
			if not ctx.get(item["if"]):
				continue
			item = item["text"]
		body.append(_fill(item, ctx))

	# facts: list of (label_key, value) — or a callable(lang) returning that list,
	# for values that themselves need translating.
	rows = facts(lang) if callable(facts) else (facts or [])
	fact_rows = [
		{"label": escape_html(label(k, lang)), "value": f"<bdi>{escape_html(str(v))}</bdi>"}
		for k, v in rows
		if v not in (None, "", 0)
	]

	cta_label = _fill(m.get("cta", ""), ctx) if m.get("cta") else ""
	cta_url = frontend_url(path) if path is not None else None
	subject = _fill(m["subject"], ctx, escape=False)

	html = frappe.render_template(
		"templates/emails/sokan_notification.html",
		{
			"lang": "fa" if rtl else "en",
			"dir": "rtl" if rtl else "ltr",
			"start": "right" if rtl else "left",
			"end": "left" if rtl else "right",
			# Web fonts are unreliable in mail clients; these stacks degrade well.
			"font": "Tahoma,'Segoe UI',Arial,sans-serif" if rtl else "'Segoe UI',Helvetica,Arial,sans-serif",
			"display": "Tahoma,Arial,sans-serif" if rtl else "Georgia,'Times New Roman',serif",
			"mono": "Tahoma,Arial,sans-serif" if rtl else "'SFMono-Regular',Menlo,Consolas,monospace",
			"subject": escape_html(subject),
			"preheader": _strip_tags(body[0]) if body else escape_html(subject),
			"eyebrow": _fill(m.get("eyebrow", ""), ctx),
			"heading": _fill(m["heading"], ctx),
			"body": body,
			"facts": fact_rows,
			# A one-time code, shown large; digits only, so no escaping concerns.
			"code": "".join(ch for ch in str(ctx.get("code") or "") if ch.isdigit())
			if "{code}" in m["subject"]
			else "",
			"cta": cta_label,
			"cta_url": cta_url,
			"link_hint": common["link_hint"],
			"note": _fill(m["note"], ctx) if m.get("note") else "",
			"signoff": common["signoff"],
			"reason": common["reason"][spec["audience"]],
			"platform": escape_html(settings.platform_name or "Sokan"),
			"site_url": site,
			"site_host": urlparse(site).netloc or site,
			"logo_url": frontend_url("/email-logo.png"),
			"support_email": settings.support_email,
			"prefs_url": frontend_url("/partner/profile") if prefs else None,
			"prefs": common["prefs"],
		},
	)
	return subject, html


def _strip_tags(html: str) -> str:
	import re

	return re.sub(r"<[^>]+>", "", html)


# --------------------------------------------------------------------------- sending


def _language(address: str) -> str:
	lang = frappe.db.get_value("User", address, "language") if frappe.db.exists("User", address) else None
	return "fa" if (lang or "").startswith("fa") else "en"


def send(
	event: str,
	to,
	ctx: dict | None = None,
	*,
	facts=None,
	path: str | None = None,
	reply_to: str | None = None,
	now: bool = False,
):
	"""Email `event` to each address in `to`, each in their own language."""
	recipients = sorted({r for r in (to or []) if r and r not in ("Administrator", "Guest")})
	if not recipients:
		return
	audience = MESSAGES[event]["audience"]
	by_lang: dict[str, list[str]] = {}
	for r in recipients:
		by_lang.setdefault(_language(r), []).append(r)
	for lang, addresses in by_lang.items():
		try:
			subject, html = render(
				event, lang, ctx or {}, facts, path, prefs=audience.startswith("forwarder")
			)
			q = frappe.sendmail(
				recipients=addresses,
				subject=subject,
				message=html,
				reply_to=reply_to or get_settings().support_email or None,
				header=None,
				with_container=False,
			)
			# Codes and reset links can't wait for the scheduled queue run, but they
			# must not be sent inside the request either: a slow or unreachable mail
			# server would hold it for Frappe's 2-minute SMTP timeout (nginx answers
			# 504 long before). A worker sends them right after the commit instead.
			if now and q:
				frappe.enqueue(
					"sokan.emails.deliver",
					queue="short",
					name=q.name,
					enqueue_after_commit=True,
				)
		except Exception:
			frappe.log_error(title=f"Sokan email failed: {event}")


def deliver(name: str):
	"""Background job: send one queued email now. Failures stay on the Email Queue
	record (status Error, with the SMTP message) and the scheduler retries them."""
	from frappe.email.doctype.email_queue.email_queue import EmailQueue

	if record := EmailQueue.find(name):
		record.send()
