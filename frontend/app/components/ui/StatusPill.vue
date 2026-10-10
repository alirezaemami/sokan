<script setup lang="ts">
const props = defineProps<{ status: string; group?: string }>()
const fmt = useFormat()

const tone = computed(() => {
  const s = props.status
  if (['Open', 'Active', 'Accepted', 'Approved', 'Booked', 'Quoted'].includes(s)) return 'bg-success/12 text-success'
  if (['New', 'Submitted', 'Unlocked'].includes(s)) return 'bg-sea/12 text-sea'
  if (['Pending', 'Draft'].includes(s)) return 'bg-warning/15 text-warning'
  if (['Rejected', 'Cancelled', 'Suspended', 'Declined'].includes(s)) return 'bg-danger/12 text-danger'
  return 'bg-sunken text-muted'
})
</script>

<template>
  <span class="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold" :class="tone">
    <span class="size-1.5 rounded-full bg-current" />
    {{ fmt.label(group || 'status', status) }}
  </span>
</template>
