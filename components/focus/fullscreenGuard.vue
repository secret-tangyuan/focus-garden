<script setup lang="ts">
import { IconMaximize, IconAlertTriangle, IconEyeOff } from '@tabler/icons-vue'
import { TimerState, useSchedule } from '~~/stores/schedule'
import { useFocusMode } from '~~/stores/focusMode'

const focusMode = useFocusMode()
const scheduleStore = useSchedule()

/** 失焦提示 */
const blurred = ref(false)
let blurTimer: ReturnType<typeof setTimeout> | null = null

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
    }
  }
}

/** 失去焦点（切窗口 / 切标签页）→ 暂停计时并提示 */
const pauseOnBlur = () => {
  if (scheduleStore.timerState !== TimerState.RUNNING) { return }

  scheduleStore.timerState = TimerState.PAUSED
  blurred.value = true

  if (blurTimer) { clearTimeout(blurTimer) }
  blurTimer = setTimeout(() => { blurred.value = false }, 4000)
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
  if (blurTimer) { clearTimeout(blurTimer) }
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

    <!-- 失焦暂停提示 -->
    <Transition
      enter-from-class="-translate-y-6 opacity-0"
      enter-active-class="transition duration-300 ease-out"
      leave-to-class="-translate-y-6 opacity-0"
      leave-active-class="transition duration-300 ease-in"
    >
      <div
        v-if="blurred"
        class="fixed left-1/2 top-6 z-[90] flex -translate-x-1/2 items-center gap-3 rounded-2xl border border-amber-200 bg-white px-5 py-3 text-sm shadow-xl"
      >
        <span class="flex h-9 w-9 items-center justify-center rounded-full bg-amber-100 text-amber-600">
          <IconEyeOff :size="20" />
        </span>
        <span class="font-bold text-slate-800">{{ $t('focus.blur.title') }}</span>
        <span class="text-xs text-slate-500">{{ $t('focus.blur.hint') }}</span>
      </div>
    </Transition>
  </Teleport>
</template>
