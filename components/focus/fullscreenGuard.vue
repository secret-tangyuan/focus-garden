<script setup lang="ts">
import { IconMaximize, IconAlertTriangle } from '@tabler/icons-vue'
import { useI18n } from 'vue-i18n'
import { TimerState, useSchedule } from '~~/stores/schedule'
import { useFocusMode } from '~~/stores/focusMode'
import { useIsland } from '~~/stores/island'

const focusMode = useFocusMode()
const scheduleStore = useSchedule()
const island = useIsland()
const { t } = useI18n()

/** 计时进行中退出了全屏 → 拦截 */
const handleChange = () => {
  focusMode.syncFullscreenState()

  if (!focusMode.enabled) { return }

  const sessionActive = scheduleStore.timerState === TimerState.RUNNING

  if (!focusMode.isFullscreen && sessionActive) {
    focusMode.markExitDuringSession()
    if (focusMode.autoPause && scheduleStore.timerState === TimerState.RUNNING) {
      scheduleStore.timerState = TimerState.PAUSED
      focusMode.markPausedByExit()
      island.show({
        title: String(t('focus.blur.title')),
        detail: String(t('focus.notice.exitPausedBody')),
        tone: 'warning',
        duration: 3800
      })
    }
  } else if (focusMode.isFullscreen) {
    focusMode.blocked = false
  }
}

/** 回到全屏：若之前因退出全屏而暂停，则自动继续 */
const backToFullscreen = async () => {
  const ok = await focusMode.requestFullscreen()
  if (ok && focusMode.pausedByExit) {
    focusMode.clearPausedByExit()
    if (scheduleStore.timerState === TimerState.PAUSED) {
      scheduleStore.timerState = TimerState.RUNNING
      island.show({
        title: String(t('focus.notice.resumedTitle')),
        detail: String(t('focus.notice.resumedBody')),
        tone: 'success'
      })
    }
  }
}

/** 失去焦点（切窗口 / 切标签页）→ 暂停计时并提示 */
const pauseOnBlur = () => {
  if (scheduleStore.timerState !== TimerState.RUNNING) { return }

  scheduleStore.timerState = TimerState.PAUSED
  island.show({
    title: String(t('focus.blur.title')),
    detail: String(t('focus.blur.hint')),
    tone: 'warning',
    duration: 4200
  })
}

const handleVisibility = () => {
  if (document.hidden) { pauseOnBlur() }
}

onMounted(() => {
  focusMode.syncFullscreenState()
  document.addEventListener('fullscreenchange', handleChange)
  document.addEventListener('visibilitychange', handleVisibility)
  window.addEventListener('blur', pauseOnBlur)
})

onBeforeUnmount(() => {
  document.removeEventListener('fullscreenchange', handleChange)
  document.removeEventListener('visibilitychange', handleVisibility)
  window.removeEventListener('blur', pauseOnBlur)
})
</script>

<template>
  <Teleport to="body">
    <!-- 退出全屏拦截 -->
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
        @click="backToFullscreen"
      >
        <IconMaximize :size="22" />
        {{ $t('focus.guard.back') }}
      </button>
      <p class="text-xs text-slate-500">{{ $t('focus.guard.exitHint') }}</p>
    </div>
  </Teleport>
</template>
