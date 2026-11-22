<script setup lang="ts">
import {
  IconAlertTriangle,
  IconCheck,
  IconPlayerPause,
  IconPlayerPlay,
  IconRefresh,
  IconTrees,
  IconUserCircle
} from '@tabler/icons-vue'
import { useIsland, type IslandTone } from '~~/stores/island'

const island = useIsland()
let hideTimer: ReturnType<typeof setTimeout> | null = null
let clockTimer: ReturnType<typeof setInterval> | null = null

/** 灵动岛常驻显示当前系统时间 */
const now = ref(new Date())
const pad = (value: number) => String(value).padStart(2, '0')
const timeText = computed(() => {
  const d = now.value
  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
})

watch(() => island.current?.id, () => {
  if (hideTimer) {
    clearTimeout(hideTimer)
    hideTimer = null
  }
  if (!island.current) { return }
  hideTimer = setTimeout(() => island.dismiss(), island.current.duration)
})

const iconFor = (tone: IslandTone) => {
  switch (tone) {
    case 'success': return IconCheck
    case 'warning': return IconAlertTriangle
    case 'garden': return IconTrees
    default: return IconUserCircle
  }
}

const dotClass = (tone: IslandTone) => {
  switch (tone) {
    case 'success': return 'bg-emerald-400'
    case 'warning': return 'bg-amber-300'
    case 'garden': return 'bg-lime-300'
    default: return 'bg-brand'
  }
}

const titleIcon = (title: string) => {
  if (title.includes('暂停') || title.toLowerCase().includes('pause')) { return IconPlayerPause }
  if (title.includes('继续') || title.toLowerCase().includes('resume')) { return IconPlayerPlay }
  if (title.includes('重置') || title.toLowerCase().includes('reset')) { return IconRefresh }
  return null
}

onMounted(() => {
  clockTimer = setInterval(() => { now.value = new Date() }, 1000)
})

onBeforeUnmount(() => {
  if (hideTimer) { clearTimeout(hideTimer) }
  if (clockTimer) { clearInterval(clockTimer) }
})
</script>

<template>
  <Teleport to="body">
    <div
      class="pointer-events-none fixed left-1/2 top-4 z-[120] -translate-x-1/2"
      aria-live="polite"
      data-testid="dynamic-island"
    >
      <div
        class="pointer-events-auto flex items-center gap-2 overflow-hidden rounded-full border border-white/10 bg-slate-950/90 px-3 py-1.5 text-white shadow-[0_12px_40px_rgba(15,23,42,0.32)] backdrop-blur"
      >
        <span class="relative flex h-2 w-2 shrink-0">
          <span
            :class="['absolute inline-flex h-full w-full animate-ping rounded-full opacity-60', island.current ? dotClass(island.current.tone) : 'bg-brand']"
          />
          <span
            :class="['relative inline-flex h-2 w-2 rounded-full', island.current ? dotClass(island.current.tone) : 'bg-brand']"
          />
        </span>
        <span
          class="shrink-0 font-mono text-xs font-bold tabular-nums text-white/90"
          data-testid="island-clock"
          v-text="timeText"
        />
        <Transition name="island-detail">
          <span
            v-if="island.current"
            class="flex min-w-0 items-center gap-1.5 whitespace-nowrap"
          >
            <component
              :is="titleIcon(island.current.title) || iconFor(island.current.tone)"
              :size="15"
              :class="['shrink-0', dotClass(island.current.tone)]"
            />
            <span class="text-xs font-bold" v-text="island.current.title" />
            <span
              v-if="island.current.detail"
              class="max-w-64 truncate text-[11px] text-white/65"
              v-text="island.current.detail"
            />
          </span>
        </Transition>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.island-detail-enter-active,
.island-detail-leave-active {
  transition:
    max-width 320ms cubic-bezier(0.22, 1, 0.36, 1),
    opacity 200ms ease;
}

.island-detail-enter-from,
.island-detail-leave-to {
  max-width: 0;
  opacity: 0;
}
</style>
