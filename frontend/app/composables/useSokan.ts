import type {
  AdminOverview,
  AdminPaged,
  AdminReports,
  Country,
  CustomerRequestDetail,
  CustomerRequestRow,
  ForwarderCard,
  ForwarderProfile,
  HomePayload,
  LeadDetail,
  LeadItem,
  Me,
  Paged,
  PartnerDashboard,
  Plan,
  Quote,
  TopUp,
  TransportMode,
  WalletSummary,
  WalletTransaction,
  Row,
} from '~/types/sokan'
import type { CaptchaChallenge } from '~/utils/captcha'

type Params = Record<string, unknown>

/**
 * Client for the whitelisted `sokan.api.*` endpoints (plus Frappe's own auth).
 *
 * Requests use relative `/api/...` paths — nuxt.config routeRules proxy those
 * to Frappe, so the browser only ever talks to this app's origin and the
 * Frappe session cookie is first-party.
 *
 * Must be called during setup: on the server it captures `useRequestFetch`,
 * which forwards the visitor's cookies to Frappe during SSR.
 */
export function useSokan() {
  const fetcher = useRequestFetch()
  const me = useMe()
  const { $i18n } = useNuxtApp()

  function headers(): Record<string, string> {
    const h: Record<string, string> = { Accept: 'application/json', 'Accept-Language': $i18n.locale.value }
    if (me.value?.csrf_token) h['X-Frappe-CSRF-Token'] = me.value.csrf_token
    return h
  }

  function get<T>(method: string, params?: Params) {
    return fetcher<{ message: T }>(`/api/method/${method}`, { params, headers: headers() }).then((r) => r.message)
  }

  function post<T>(method: string, body?: Params) {
    return fetcher<{ message: T }>(`/api/method/${method}`, { method: 'POST', body: body ?? {}, headers: headers() }).then(
      (r) => r.message,
    )
  }

  const pub = (m: string) => `sokan.api.public.${m}`
  const cust = (m: string) => `sokan.api.customer.${m}`
  const part = (m: string) => `sokan.api.partner.${m}`
  const auth = (m: string) => `sokan.api.auth.${m}`
  const adm = (m: string) => `sokan.api.admin.${m}`

  return {
    get,
    post,

    // ---- public
    home: () => get<HomePayload>(pub('get_home')),
    modes: () => get<TransportMode[]>(pub('list_transport_modes')),
    plans: () => get<Plan[]>(pub('list_plans')),
    countries: () => get<Country[]>(pub('list_countries')),
    forwarders: (p: { search?: string; mode?: string; country?: string; page?: number; page_size?: number }) =>
      get<Paged<ForwarderCard>>(pub('list_forwarders'), p),
    forwarder: (slug: string) => get<ForwarderProfile>(pub('get_forwarder'), { slug }),
    contact: (p: Params) => post<{ name: string }>(pub('submit_contact'), p),

    // ---- auth
    me: () => get<Me>(auth('me')),
    registerCustomer: (p: Params) => post<Me>(auth('register_customer'), p),
    registerForwarder: (p: Params) => post<Me>(auth('register_forwarder'), p),
    becomeCustomer: (p: Params = {}) => post<Me>(auth('become_customer'), p),
    login: (usr: string, pwd: string, captcha: string) =>
      post<{ message: string; full_name: string }>('login', { usr, pwd, captcha }),
    captchaChallenge: () => get<CaptchaChallenge>(auth('captcha_challenge')),
    sendVerificationCode: (force = false) =>
      post<{ verified: boolean; email?: string; sent?: boolean; resend_in?: number }>(auth('send_verification_code'), {
        force: force ? 1 : 0,
      }),
    verifyEmail: (code: string) => post<Me>(auth('verify_email'), { code }),
    logout: () => post<unknown>('logout'),
    // Sokan's own reset flow: branded email, link back to this site.
    forgotPassword: (email: string, captcha: string) => post<{ ok: boolean }>(auth('forgot_password'), { email, captcha }),
    resetPassword: (key: string, new_password: string) => post<Me>(auth('reset_password'), { key, new_password }),

    // ---- customer
    customer: {
      dashboard: () =>
        get<{ counts: Record<string, number>; quotes_waiting: number; recent: CustomerRequestRow[] }>(cust('dashboard')),
      requests: (p: { status?: string; page?: number }) => get<Paged<CustomerRequestRow>>(cust('list_requests'), p),
      request: (name: string) => get<CustomerRequestDetail>(cust('get_request'), { name }),
      create: (data: Params, publish = 1) =>
        post<{ name: string; status: string; leads_sent: number; needs_verification?: boolean }>(cust('create_request'), {
          data,
          publish,
        }),
      accept: (quote: string) => post<CustomerRequestDetail>(cust('accept_quote'), { quote }),
      reject: (quote: string, reason?: string) => post<CustomerRequestDetail>(cust('reject_quote'), { quote, reason }),
      cancel: (name: string, reason?: string) => post<CustomerRequestDetail>(cust('cancel_request'), { name, reason }),
      publish: (name: string) => post<CustomerRequestDetail>(cust('publish_request'), { name }),
      review: (request: string, rating: number, comment?: string) =>
        post<{ rating: number; comment: string }>(cust('leave_review'), { request, rating, comment }),
      profile: () => get<Record<string, any>>(cust('get_profile')),
      updateProfile: (data: Params) => post<Record<string, any>>(cust('update_profile'), { data }),
    },

    // ---- partner (forwarder)
    partner: {
      dashboard: () => get<PartnerDashboard>(part('dashboard')),
      leads: (p: { status?: string; mode?: string; only_open?: number; page?: number }) =>
        get<Paged<LeadItem>>(part('list_leads'), p),
      lead: (request: string) => get<LeadDetail>(part('get_lead'), { request }),
      unlock: (request: string) => post<LeadDetail>(part('unlock_lead'), { request }),
      decline: (request: string, reason?: string) => post<{ ok: boolean }>(part('decline_lead'), { request, reason }),
      quote: (request: string, data: Params) => post<LeadDetail>(part('submit_quote'), { request, data }),
      withdraw: (request: string) => post<LeadDetail>(part('withdraw_quote'), { request }),
      quotes: (p: { status?: string; page?: number }) => get<Paged<Quote>>(part('list_quotes'), p),
      wallet: (p: { page?: number } = {}) =>
        get<{
          summary: WalletSummary
          transactions: WalletTransaction[]
          total: number
          topups: TopUp[]
          instructions: string | null
        }>(part('wallet'), p),
      topup: (p: Params) => post<{ name: string; status: string }>(part('request_topup'), p),
      changePlan: (plan: string) => post<WalletSummary>(part('change_plan'), { plan }),
      profile: () => get<Record<string, any>>(part('get_profile')),
      updateProfile: (data: Params) => post<Record<string, any>>(part('update_profile'), { data }),
    },

    // ---- admin (managers). Every endpoint re-checks the role server-side.
    admin: {
      overview: () => get<AdminOverview>(adm('overview')),
      attention: () => get<AdminOverview['attention']>(adm('attention')),
      reports: (p: { from_date?: string; to_date?: string }) => get<AdminReports>(adm('reports'), p),
      forwarders: (p: Params) => get<AdminPaged>(adm('list_forwarders'), p),
      forwarder: (name: string) => get<Row>(adm('get_forwarder'), { name }),
      setForwarderStatus: (name: string, status: string, reason?: string) => post<Row>(adm('set_forwarder_status'), { name, status, reason }),
      updateForwarder: (name: string, data: Params) => post<Row>(adm('update_forwarder'), { name, data }),
      adjustWallet: (name: string, amount: number, note: string) => post<Row>(adm('adjust_wallet'), { name, amount, note }),
      customers: (p: Params) => get<AdminPaged>(adm('list_customers'), p),
      customer: (name: string) => get<Row>(adm('get_customer'), { name }),
      markEmailVerified: (user: string) => post<{ user: string; email_verified: boolean }>(adm('mark_email_verified'), { user }),
      setCustomerBlocked: (name: string, blocked: boolean) => post<Row>(adm('set_customer_blocked'), { name, blocked: blocked ? 1 : 0 }),
      requests: (p: Params) => get<AdminPaged>(adm('list_requests'), p),
      request: (name: string) => get<Row>(adm('get_request'), { name }),
      cancelRequest: (name: string, reason: string) => post<Row>(adm('cancel_request'), { name, reason }),
      topups: (p: Params) => get<AdminPaged>(adm('list_topups'), p),
      reviewTopup: (name: string, action: 'approve' | 'reject', note?: string) => post<Row>(adm('review_topup'), { name, action, note }),
      reviews: (p: Params) => get<AdminPaged>(adm('list_reviews'), p),
      moderateReview: (name: string, action: 'approve' | 'reject', note?: string) => post<Row>(adm('moderate_review'), { name, action, note }),
      messages: (p: Params) => get<AdminPaged>(adm('list_messages'), p),
      setMessageStatus: (name: string, status: string) => post<Row>(adm('set_message_status'), { name, status }),
      transactions: (p: Params) => get<AdminPaged & { credits: number; debits: number; currency: string }>(adm('list_transactions'), p),
      plans: () => get<Row[]>(adm('list_plans')),
      savePlan: (data: Params) => post<Row[]>(adm('save_plan'), { data }),
      modes: () => get<Row[]>(adm('list_modes')),
      saveMode: (name: string, data: Params) => post<Row[]>(adm('save_mode'), { name, data }),
      settings: () => get<Row>(adm('get_settings')),
      updateSettings: (data: Params) => post<Row>(adm('update_settings'), { data }),
      managers: () => get<Row[]>(adm('list_managers')),
      addManager: (email: string, full_name?: string) => post<Row[]>(adm('add_manager'), { email, full_name }),
      removeManager: (user: string) => post<Row[]>(adm('remove_manager'), { user }),
    },
  }
}

/** Upload a file to Frappe and return its URL (public by default). */
export async function uploadFile(file: File, opts: { isPrivate?: boolean; csrf?: string } = {}) {
  const form = new FormData()
  form.append('file', file, file.name)
  form.append('is_private', opts.isPrivate ? '1' : '0')
  const res = await $fetch<{ message: { file_url: string } }>('/api/method/upload_file', {
    method: 'POST',
    body: form,
    headers: opts.csrf ? { 'X-Frappe-CSRF-Token': opts.csrf } : undefined,
  })
  return res.message.file_url
}
