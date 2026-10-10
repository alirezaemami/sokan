<script setup lang="ts">
import type { Plan } from '~/types/sokan'

const props = defineProps<{ plan: Plan; current?: boolean; highlight?: boolean }>()
defineEmits<{ choose: [] }>()
const fmt = useFormat()
const featured = computed(() => props.highlight ?? Boolean(props.plan.badge))
</script>

<template>
  <TiltCard class="h-full rounded-3xl">
    <div
      class="relative flex h-full flex-col overflow-hidden rounded-3xl p-7 transition-shadow"
      :class="featured ? 'bg-night-950 text-white shadow-2xl shadow-brand/25 ring-2 ring-brand' : 'card'"
    >
      <AuroraBackground v-if="featured" :grid="false" />
      <div class="relative flex items-center justify-between gap-3">
        <h3 class="text-xl font-extrabold">{{ plan.name }}</h3>
        <span v-if="plan.badge" class="rounded-full bg-coral px-3 py-1 text-xs font-bold text-white">{{ plan.badge }}</span>
        <span v-else-if="current" class="rounded-full bg-success/15 px-3 py-1 text-xs font-bold text-success">{{ $t('pricing.current') }}</span>
      </div>
      <p class="relative mt-2 text-sm" :class="featured ? 'text-white/65' : 'text-muted'">{{ plan.description }}</p>

      <p class="relative mt-6 flex items-baseline gap-1.5">
        <span class="text-4xl font-black tracking-tight">{{ plan.monthly_fee ? fmt.money(plan.monthly_fee, plan.currency) : $t('pricing.free') }}</span>
        <span v-if="plan.monthly_fee" class="text-sm" :class="featured ? 'text-white/55' : 'text-faint'">/ {{ $t('pricing.month') }}</span>
      </p>

      <dl class="relative mt-6 grid grid-cols-2 gap-3 rounded-2xl p-4 text-sm" :class="featured ? 'bg-white/6' : 'bg-sunken'">
        <div>
          <dt :class="featured ? 'text-white/55' : 'text-faint'">{{ $t('pricing.unlockFee') }}</dt>
          <dd class="mt-0.5 font-bold">{{ fmt.money(plan.view_fee, plan.currency) }}</dd>
        </div>
        <div>
          <dt :class="featured ? 'text-white/55' : 'text-faint'">{{ $t('pricing.quoteFee') }}</dt>
          <dd class="mt-0.5 font-bold">{{ plan.quote_fee ? fmt.money(plan.quote_fee, plan.currency) : $t('pricing.free') }}</dd>
        </div>
        <div class="col-span-2 text-xs" :class="featured ? 'text-white/65' : 'text-muted'">
          {{ $t('pricing.included', { views: fmt.number(plan.free_views_per_month), quotes: fmt.number(plan.free_quotes_per_month) }) }}
        </div>
      </dl>

      <ul class="relative mt-6 flex-1 space-y-3 text-sm">
        <li v-for="feat in plan.features" :key="feat" class="flex items-start gap-2.5">
          <AppIcon name="circle-check" :size="18" class="mt-0.5 shrink-0" :class="featured ? 'text-lagoon' : 'text-success'" />
          {{ feat }}
        </li>
      </ul>

      <div class="relative mt-8">
        <slot>
          <AppButton to="/register/forwarder" :variant="featured ? 'accent' : 'secondary'" block icon-end="arrow-right">{{ $t('pricing.start') }}</AppButton>
        </slot>
      </div>
    </div>
  </TiltCard>
</template>
