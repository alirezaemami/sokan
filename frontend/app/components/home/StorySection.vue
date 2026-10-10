<script setup lang="ts">
/**
 * Three reasons shippers use Sokan, told against photography. On desktop the
 * photo is pinned and crossfades as each reason scrolls into the middle of
 * the screen; on phones every reason carries its own photo inline. All text
 * is in the server markup; only the active highlight needs JS.
 */
import type { PhotoKey } from '~/utils/photos'

const fmt = useFormat()
const steps: { key: 's1' | 's2' | 's3'; photo: PhotoKey; icon: string }[] = [
  { key: 's1', photo: 'warehouse', icon: 'receipt' },
  { key: 's2', photo: 'contract', icon: 'shield-check' },
  { key: 's3', photo: 'ship', icon: 'handshake' },
]

const active = ref(0)
const items = ref<HTMLElement[]>([])
let observer: IntersectionObserver | null = null
onMounted(() => {
  observer = new IntersectionObserver(
    (entries) => {
      for (const e of entries) if (e.isIntersecting) active.value = Number((e.target as HTMLElement).dataset.index)
    },
    // A step is "current" while it crosses the middle band of the screen.
    { rootMargin: '-45% 0px -45% 0px' },
  )
  items.value.forEach((el) => observer!.observe(el))
})
onBeforeUnmount(() => observer?.disconnect())

// Example figures for the floating cards (labelled as an example).
const lines = [
  { k: 'freight', v: 2100 },
  { k: 'origin', v: 180 },
  { k: 'docs', v: 45 },
]
const total = lines.reduce((a, l) => a + l.v, 0)
</script>

<template>
  <section id="why" class="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8 lg:py-28">
    <SectionHeading :eyebrow="$t('home.story.eyebrow')" :title="$t('home.story.title')" :subtitle="$t('home.story.subtitle')" />

    <div class="mt-14 grid gap-10 lg:grid-cols-2 lg:gap-16">
      <!-- Reasons -->
      <ol class="space-y-14 lg:space-y-0">
        <li
          v-for="(s, i) in steps"
          :key="s.key"
          ref="items"
          :data-index="i"
          class="flex flex-col justify-center lg:min-h-[64vh]"
        >
          <div v-reveal class="photo-wipe relative mb-6 overflow-hidden rounded-2xl lg:hidden">
            <ChartPhoto :name="s.photo" :alt="$t(`photos.${s.photo}`)" sizes="100vw" class="aspect-[16/10]" />
          </div>
          <div class="transition-opacity duration-500" :class="active === i ? 'lg:opacity-100' : 'lg:opacity-35'">
            <span class="grid size-12 place-items-center rounded-full border-2 transition-colors duration-500" :class="active === i ? 'border-buoy bg-buoy text-white' : 'border-sea text-sea'">
              <AppIcon :name="s.icon" :size="21" />
            </span>
            <h3 class="font-display mt-5 text-3xl text-ink sm:text-4xl">{{ $t(`home.story.${s.key}.title`) }}</h3>
            <p class="mt-3 max-w-md text-lg leading-relaxed text-muted">{{ $t(`home.story.${s.key}.text`) }}</p>
          </div>
        </li>
      </ol>

      <!-- Pinned photo (desktop) -->
      <div class="hidden lg:block">
        <div class="sticky top-[calc(50vh-17rem)] h-[34rem]">
          <div class="relative size-full overflow-hidden rounded-3xl shadow-2xl">
            <ChartPhoto
              v-for="(s, i) in steps"
              :key="s.photo"
              :name="s.photo"
              alt=""
              sizes="600px"
              class="absolute inset-0 transition-opacity duration-700"
              :class="active === i ? 'opacity-100' : 'opacity-0'"
              img-class="drift"
            />
            <div class="pointer-events-none absolute inset-0 bg-gradient-to-t from-night-950/60 via-transparent to-transparent" />
            <p class="chart-label absolute start-5 top-5 rounded-full bg-night-950/55 px-2.5 py-1 text-white backdrop-blur">{{ $t('home.visual.example') }}</p>

            <!-- Floating example card for the current reason -->
            <Transition mode="out-in" enter-active-class="transition duration-500 ease-[var(--ease-spring)]" enter-from-class="opacity-0 translate-y-4" leave-active-class="transition duration-200" leave-to-class="opacity-0">
              <div :key="active" class="glass absolute inset-x-5 bottom-5 rounded-2xl p-4 shadow-xl">
                <template v-if="active === 0">
                  <p class="chart-label text-faint">{{ $t('home.story.card.quote') }}</p>
                  <dl class="mt-2 space-y-1 text-sm">
                    <div v-for="l in lines" :key="l.k" class="flex justify-between"><dt class="text-muted">{{ $t(`home.story.card.${l.k}`) }}</dt><dd class="tabular-nums">{{ fmt.money(l.v, 'USD') }}</dd></div>
                    <div class="flex justify-between border-t border-line pt-1 font-semibold"><dt>{{ $t('home.story.card.total') }}</dt><dd class="font-display text-lg tabular-nums">{{ fmt.money(total, 'USD') }}</dd></div>
                  </dl>
                </template>
                <div v-else-if="active === 1" class="flex items-center gap-3">
                  <span class="font-display grid size-11 shrink-0 place-items-center rounded-full bg-sea/12 text-lg text-sea">B</span>
                  <div class="min-w-0 flex-1">
                    <p class="flex items-center gap-1.5 font-semibold">BlueWake Freight <AppIcon name="badge-check" :size="16" class="text-sea" /></p>
                    <p class="text-xs text-muted">{{ $t('home.story.card.verified') }} · ★ {{ fmt.number(4.8, 1) }}</p>
                  </div>
                </div>
                <div v-else class="flex items-center gap-3">
                  <span class="grid size-11 shrink-0 place-items-center rounded-full bg-starboard text-white"><AppIcon name="check" :size="20" /></span>
                  <div class="min-w-0 flex-1">
                    <p class="font-semibold">{{ $t('home.story.card.booked') }}</p>
                    <p class="text-xs text-muted">{{ $t('home.story.card.bookedText') }}</p>
                  </div>
                </div>
              </div>
            </Transition>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
