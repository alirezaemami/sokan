<script setup lang="ts">
/**
 * Icon by name. Backend data (transport modes) names icons as strings, so a
 * registry maps kebab-case names to explicitly imported Lucide components —
 * only these ship in the bundle.
 */
import {
  Anchor, ArrowLeft, ArrowRight, ArrowUpRight, Award, BadgeCheck, Ban, Bell, Boxes, Building, Calendar,
  ChartColumn, Check, ChevronDown, ChevronLeft, ChevronRight, CircleCheck, CircleDollarSign, CircleQuestionMark,
  Clock, Coins, Construction, Container, CreditCard, Earth, ExternalLink, Eye, FileText, Flame, Funnel, Gauge,
  Globe, Handshake, Inbox, Info, Languages, LayoutDashboard, Layers, Link2, ListChecks, LoaderCircle, Lock,
  LockOpen, LogOut, Mail, MapPin, Menu, MessageSquare, Minus, Moon, Package, Phone, Plane, Plus, Quote, Receipt,
  Rocket, RotateCcw, Route, Scale, Search, Send, Settings, ShieldCheck, Ship, SlidersHorizontal, Sparkles, Star,
  Sun, Target, Thermometer, Timer, TrainFront, Trash, TrendingUp, TriangleAlert, Truck, Upload, User, Users,
  Wallet, X, Zap,
} from '@lucide/vue'

const REGISTRY = {
  anchor: Anchor, 'arrow-left': ArrowLeft, 'arrow-right': ArrowRight, 'arrow-up-right': ArrowUpRight, award: Award,
  'badge-check': BadgeCheck, ban: Ban, bell: Bell, boxes: Boxes, building: Building, calendar: Calendar,
  chart: ChartColumn, check: Check, 'chevron-down': ChevronDown, 'chevron-left': ChevronLeft,
  'chevron-right': ChevronRight, 'circle-check': CircleCheck, dollar: CircleDollarSign, help: CircleQuestionMark,
  clock: Clock, coins: Coins, construction: Construction, container: Container, 'credit-card': CreditCard,
  earth: Earth, 'external-link': ExternalLink, eye: Eye, 'file-text': FileText, flame: Flame, filter: Funnel,
  gauge: Gauge, globe: Globe, handshake: Handshake, inbox: Inbox, info: Info, languages: Languages,
  dashboard: LayoutDashboard, layers: Layers, link: Link2, 'list-checks': ListChecks, loader: LoaderCircle,
  lock: Lock, 'lock-open': LockOpen, 'log-out': LogOut, mail: Mail, 'map-pin': MapPin, menu: Menu,
  message: MessageSquare, minus: Minus, moon: Moon, package: Package, phone: Phone, plane: Plane, plus: Plus,
  quote: Quote, receipt: Receipt, rocket: Rocket, undo: RotateCcw, route: Route, scale: Scale, search: Search,
  send: Send, settings: Settings, 'shield-check': ShieldCheck, ship: Ship, sliders: SlidersHorizontal,
  sparkles: Sparkles, star: Star, sun: Sun, target: Target, thermometer: Thermometer, timer: Timer,
  'train-front': TrainFront, trash: Trash, 'trending-up': TrendingUp, alert: TriangleAlert, truck: Truck,
  upload: Upload, user: User, users: Users, wallet: Wallet, x: X, zap: Zap,
} as const

export type IconName = keyof typeof REGISTRY

const props = withDefaults(defineProps<{ name: string; size?: number | string; strokeWidth?: number; flip?: boolean }>(), {
  size: 20,
  strokeWidth: 1.9,
  flip: false,
})

const component = computed(() => REGISTRY[props.name as IconName] ?? Package)
</script>

<template>
  <component
    :is="component"
    :size="Number(size)"
    :stroke-width="strokeWidth"
    :class="{ 'flip-rtl': flip }"
    aria-hidden="true"
    focusable="false"
  />
</template>
