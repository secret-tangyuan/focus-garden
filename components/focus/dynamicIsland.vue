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

const toneClass = (tone: IslandTone) => {
  switch (tone) {
    case 'success': return 'text-emerald-400'
    case 'warning': return 'text-amber-300'
    case 'garden': return 'text-lime-300'
    default: return 'text-brand'
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

onBeforeUnmount(() => {
  if (hideTimer) { clearTimeout(hideTimer) }
})
</script>

<template>
  <Teleport to="body">
    <div
      class="pointer-events-none fixed left-1/2 top-4 z-[120] -translate-x-1/2"
      aria-live="polite"
      data-testid="dynamic-island"
    >
      <Transition
        appear
        enter-from-class="dynamic-island-enter-from"
        enter-active-class="dynamic-island-enter-active"
        leave-to-class="dynamic-island-leave-to"
        leave-active-class="dynamic-island-leave-active"
      >
        <button
          v-if="island.current"
          type="button"
          class="pointer-events-auto flex max-w-[min(92vw,34rem)] items-center gap-2.5 rounded-full border border-white/10 bg-slate-950 px-4 py-2.5 text-white shadow-[0_12px_40px_rgba(15,23,42,0.34)]"
          :aria-label="$t('settings.buttons.close')"
          @click="island.dismiss()"
        >
          <span class="relative flex h-2.5 w-2.5 shrink-0">
            <span :class="['absolute inline-flex h-full w-full animate-ping rounded-full opacity-60', dotClass(island.current.tone)]" />
            <span :class="['relative inline-flex h-2.5 w-2.5 rounded-full', dotClass(island.current.tone)]" />
          </span>
          <component
            :is="titleIcon(island.current.title) || iconFor(island.current.tone)"
            :size="16"
            :class="['shrink-0', toneClass(island.current.tone)]"
          />
          <span class="truncate text-xs font-bold">{{ island.current.title }}</span>
          <span
            v-if="island.current.detail"
            class="truncate text-[11px] text-white/65"
          >{{ island.current.detail }}</span>
        </button>
      </Transition>
    </div>
  </Teleport>
</template>

<style scoped>
.dynamic-island-enter-active,
.dynamic-island-leave-active {
  transition:
    opacity 220ms ease,
    transform 320ms cubic-bezier(0.22, 1, 0.36, 1),
    filter 220ms ease;
}

.dynamic-island-enter-from,
.dynamic-island-leave-to {
  opacity: 0;
  transform: translateY(-12px) scale(0.72);
  filter: blur(8px);
}
</style>
