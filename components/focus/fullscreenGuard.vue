<script setup lang="ts">
import { IconMaximize, IconAlertTriangle } from '@tabler/icons-vue'
import { TimerState, useSchedule } from '~~/stores/schedule'
import { useFocusMode } from '~~/stores/focusMode'

const focusMode = useFocusMode()
const scheduleStore = useSchedule()

/** 计时进行中退出了全屏 → 拦截 */
const handleChange = () => {
  focusMode.syncFullscreenState()

  if (!focusMode.enabled) { return }

  const sessionActive = scheduleStore.timerState === TimerState.RUNNING

  if (!focusMode.isFullscreen && sessionActive) {
    focusMode.markExitDuringSession()
    if (focusMode.autoPause && scheduleStore.timerState === TimerState.RUNNING) {
      scheduleStore.timerState = TimerState.PAUSED
    }
  } else if (focusMode.isFullscreen) {
    focusMode.blocked = false
  }
}

onMounted(() => {
  focusMode.syncFullscreenState()
  document.addEventListener('fullscreenchange', handleChange)
})

onBeforeUnmount(() => {
  document.removeEventListener('fullscreenchange', handleChange)
})
</script>

<template>
  <Teleport to="body">
    <div
      v-if="focusMode.needsFullscreen"
      class="fixed inset-0 z-[100] flex flex-col items-center justify-center gap-6 bg-slate-900/95 px-6 text-center"
    >
      <IconAlertTriangle :size="56" class="text-amber-300" />
      <h2 class="text-2xl font-bold text-white">{{ $t('focus.guard.title') }}</h2>
      <p class="max-w-md text-sm leading-relaxed text-slate-300">
        <strong class="text-slate-100">{{ $t('focus.guard.strong') }}</strong>
        <span class="ml-1 text-slate-400">{{ $t('focus.guard.hint') }}</span>
      </p>
      <button
        class="flex items-center gap-2 rounded-full bg-brand-strong px-7 py-3 text-base font-bold text-white shadow-lg transition hover:brightness-110"
        @click="focusMode.requestFullscreen()"
      >
        <IconMaximize :size="22" />
        {{ $t('focus.guard.back') }}
      </button>
      <p class="text-xs text-slate-500">{{ $t('focus.guard.exitHint') }}</p>
    </div>
  </Teleport>
</template>
