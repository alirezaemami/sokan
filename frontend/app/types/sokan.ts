/** Shapes returned by the whitelisted `sokan.api.*` endpoints. */

export interface TransportMode {
  name: string
  code: string
  category: 'Sea' | 'Air' | 'Road' | 'Rail' | 'Courier' | 'Multimodal'
  icon: string
  uses_containers: 0 | 1
  description?: string
}

export interface Place {
  city: string | null
  country: string | null
  country_code: string | null
  port?: string | null
}

export interface ContainerLine {
  type: string
  qty: number
  weight_kg: number
}

export interface CargoSummary {
  commodity: string
  category: string
  containers: ContainerLine[]
  total_packages: number
  total_weight_kg: number
  total_volume_cbm: number
  chargeable_weight_kg: number
  is_stackable: boolean
}

export type RequestStatus = 'Draft' | 'Open' | 'Booked' | 'Expired' | 'Cancelled'
export type LeadStatus = 'New' | 'Unlocked' | 'Quoted' | 'Declined' | 'Closed'
export type QuoteStatus = 'Submitted' | 'Accepted' | 'Rejected' | 'Withdrawn' | 'Expired'

export interface RequestTeaser {
  name: string
  title: string
  status: RequestStatus
  mode: TransportMode | null
  incoterm: string | null
  origin: Place
  destination: Place
  pickup_required: boolean
  delivery_required: boolean
  ready_date: string
  valid_until: string | null
  published_on: string | null
  cargo: CargoSummary
  services: { customs: boolean; insurance: boolean; warehousing: boolean; packing: boolean }
  quote_count: number
  quote_currency: string | null
}

export interface PackageLine {
  type: string
  qty: number
  length_cm: number
  width_cm: number
  height_cm: number
  weight_kg: number
  volume_cbm: number
}

export interface RequestFull extends RequestTeaser {
  pickup_address: string | null
  delivery_address: string | null
  hs_code: string | null
  un_number: string | null
  temperature_range: string | null
  cargo_value: number
  cargo_currency: string | null
  packages: PackageLine[]
  notes: string | null
  attachment: string | null
  contact: { name: string | null; email: string | null; phone: string | null; company: string | null }
}

export interface ForwarderCard {
  name: string
  slug: string
  company_name: string
  tagline: string | null
  logo: string | null
  country: string | null
  country_code: string | null
  city: string | null
  is_verified: boolean
  rating: number
  review_count: number
  established_year: number | null
  modes?: string[]
  contact?: { email: string; phone: string | null; website: string | null; address: string | null }
}

export interface ForwarderProfile extends Omit<ForwarderCard, 'modes'> {
  about: string | null
  cover_image: string | null
  website: string | null
  team_size: string | null
  certifications: string[]
  modes: TransportMode[]
  coverage: { name: string; code: string }[]
  stats: { quotes_sent: number; quotes_won: number; win_rate: number | null }
  meta_description: string | null
  reviews: { customer_name: string; rating: number; comment: string | null; creation: string }[]
}

export interface QuoteCharge {
  group: string
  description: string
  basis: string
  quantity: number
  unit_price: number
  amount: number
}

export interface Quote {
  name: string
  request: string
  status: QuoteStatus
  currency: string
  total_amount: number
  transit_days_min: number | null
  transit_days_max: number | null
  valid_until: string
  carrier: string | null
  routing: string | null
  free_days: number | null
  service_level: string | null
  inclusions: string | null
  exclusions: string | null
  notes: string | null
  creation: string
  charges: QuoteCharge[]
  forwarder?: ForwarderCard
  priority?: boolean
  request_title?: string
}

export interface Plan {
  name: string
  badge: string | null
  currency: string
  monthly_fee: number
  view_fee: number
  quote_fee: number
  free_views_per_month: number
  free_quotes_per_month: number
  priority_listing: 0 | 1
  description: string | null
  is_default: 0 | 1
  features: string[]
}

export interface LiveRequest {
  origin: Place
  destination: Place
  mode: TransportMode | null
  category: string
  published_on: string
  quote_count: number
  status: RequestStatus
}

export interface HomePayload {
  stats: { forwarders: number; requests: number; quotes: number; countries: number }
  modes: TransportMode[]
  featured: ForwarderCard[]
  live: LiveRequest[]
  plans: Plan[]
}

export interface Paged<T> {
  items: T[]
  total: number
  page?: number
  page_size?: number
}

export interface Me {
  user: string | null
  full_name?: string
  image?: string | null
  is_admin?: boolean
  csrf_token?: string
  customer?: { name: string; full_name: string; company_name: string | null; is_blocked: 0 | 1 } | null
  forwarder?: {
    name: string
    company_name: string
    slug: string
    status: 'Pending' | 'Active' | 'Suspended' | 'Rejected'
    logo: string | null
    wallet_balance: number
    wallet_currency: string
  } | null
}

export interface WalletSummary {
  balance: number
  currency: string
  plan: string | null
  plan_renews_on: string | null
  view_fee: number
  quote_fee: number
  monthly_fee: number
  free_views_left: number
  free_quotes_left: number
  low_balance: boolean
}

export interface WalletTransaction {
  name: string
  transaction_type: string
  amount: number
  balance_after: number
  currency: string
  posting_date: string
  description: string | null
  reference_doctype: string | null
  reference_name: string | null
}

export interface TopUp {
  name: string
  amount: number
  currency: string
  payment_method: string
  payment_reference: string | null
  status: 'Pending' | 'Approved' | 'Rejected'
  creation: string
  note: string | null
}

export interface LeadItem extends RequestTeaser {
  lead: { name: string; status: LeadStatus; sent_on: string; is_new: boolean; quote: string | null }
}

export interface LeadDetail {
  request: RequestFull | RequestTeaser
  lead: { name: string; status: LeadStatus; unlocked: boolean; unlocked_on: string | null; unlock_fee: number; was_free: 0 | 1 }
  my_quote: Quote | null
  won: boolean
  competition: { quotes: number; unlocks: number }
  pricing: {
    unlock_fee: number
    quote_fee: number
    free_views_left: number
    free_quotes_left: number
    balance: number
    currency: string
  }
  default_currency: string
}

export interface PartnerDashboard {
  company: {
    name: string
    company_name: string
    status: 'Pending' | 'Active' | 'Suspended' | 'Rejected'
    slug: string
    logo: string | null
    is_verified: 0 | 1
    rejection_reason: string | null
    profile_complete: number
  }
  wallet: WalletSummary
  stats: {
    leads_received: number
    leads_unlocked: number
    quotes_sent: number
    quotes_won: number
    win_rate: number
    rating: number
    review_count: number
    actionable: number
    by_status: Record<string, number>
  }
  recent: LeadItem[]
}

export interface CustomerRequestRow extends RequestTeaser {
  best_quote: { total_amount: number; currency: string } | null
  leads_sent: number
  unlock_count: number
  creation: string
}

export interface CustomerRequestDetail {
  request: RequestFull
  leads_sent: number
  unlock_count: number
  accepted_quote: string | null
  cancel_reason: string | null
  quotes: Quote[]
  review: { rating: number; comment: string | null; status?: 'Pending' | 'Approved' | 'Rejected' } | null
}

export interface Country {
  name: string
  code: string
}

// ---------------------------------------------------------------- admin

export type Row = Record<string, any>

export interface AdminPaged<T = Row> extends Paged<T> {
  counts?: Record<string, number>
}

export interface AdminOverview {
  currency: string
  kpis: {
    forwarders_active: number
    forwarders_total: number
    customers: number
    requests_open: number
    requests_booked: number
    requests_total: number
    quotes: number
    revenue_month: number
    revenue_last_month: number
    revenue_total: number
    wallet_float: number
  }
  attention: { forwarders: number; topups: number; topups_amount: number; reviews: number; messages: number }
  series: { date: string; requests: number; quotes: number; revenue: number }[]
  recent_requests: Row[]
  pending_forwarders: Row[]
}

export interface AdminReports {
  from_date: string
  to_date: string
  currency: string
  funnel: { published: number; leads: number; unlocks: number; quotes: number; booked: number }
  revenue: Record<'unlocks' | 'quotes' | 'subscriptions' | 'topups' | 'bonuses' | 'refunds' | 'adjustments', number>
  averages: { leads_per_request: number; quotes_per_request: number; booking_rate: number }
  monthly: { month: string; revenue: number; topups: number; requests: number; booked: number }[]
  lanes: { origin_country: string; destination_country: string; requests: number; booked: number }[]
  modes: { mode: string; requests: number; booked: number }[]
  top_forwarders: { name: string; company_name: string; country: string; quotes: number; won: number; unlocks: number; fees: number }[]
}
