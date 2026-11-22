<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { useSchedule } from '~~/stores/schedule'
import { useSettings } from '~~/stores/settings'

const scheduleStore = useSchedule()
const settingsStore = useSettings()
const { t } = useI18n()

const currentWorkMinutes = computed(() => Math.round(settingsStore.schedule.lengths.work / 60000))
const currentShortPauseMinutes = computed(() => Math.round(settingsStore.schedule.lengths.shortpause / 60000))

const WORK_MIN = 5
const WORK_MAX = 180
const WORK_STEP = 5
const PAUSE_MIN = 5
const PAUSE_MAX = 30
const PAUSE_STEP = 5

const workPercent = computed(() => ((currentWorkMinutes.value - WORK_MIN) / (WORK_MAX - WORK_MIN)) * 100)
const pausePercent = computed(() => ((currentShortPauseMinutes.value - PAUSE_MIN) / (PAUSE_MAX - PAUSE_MIN)) * 100)

const durationLabel = (minutes: number) => {
  const hours = Math.floor(minutes / 60)
  const rest = minutes % 60
  if (hours && rest) { return `${hours} ${t('focus.hours')} ${rest} ${t('focus.minutes')}` }
  if (hours) { return `${hours} ${t('focus.hours')}` }
  return `${minutes} ${t('focus.minutes')}`
}

const applyWork = (minutes: number) => {
  const ms = minutes * 60 * 1000
  settingsStore.schedule.lengths.work = ms

  // 当前正在进行的专注段同步改时长
  if (scheduleStore.getCurrentItem.type === 'work') {
    scheduleStore.lockInfo({ index: 0, length: ms, type: 'work' })
    scheduleStore.items[0].timeElapsed = 0
  }
}

const applyPause = (minutes: number) => {
  settingsStore.schedule.lengths.shortpause = minutes * 60 * 1000
  settingsStore.schedule.lengths.longpause = minutes * 60 * 1000

  if (scheduleStore.getCurrentItem.type !== 'work') {
    scheduleStore.lockInfo({ index: 0, length: minutes * 60 * 1000 })
    scheduleStore.items[0].timeElapsed = 0
  }
}

const onWorkInput = (event: Event) => {
  applyWork(Number((event.target as HTMLInputElement).value))
}

const onPauseInput = (event: Event) => {
  applyPause(Number((event.target as HTMLInputElement).value))
}
</script>

<template>
  <div class="flex w-full max-w-md flex-col gap-3">
    <label class="time-slider-group">
      <span class="flex items-center justify-between text-xs font-bold text-slate-500">
        <span>{{ $t('focus.workLength') }}</span>
        <strong class="text-brand-strong">{{ durationLabel(currentWorkMinutes) }}</strong>
      </span>
      <span class="time-slider-wrap" :style="{ '--slider-percent': workPercent + '%' }">
        <span class="time-slider-bubble">{{ durationLabel(currentWorkMinutes) }}</span>
        <input
          type="range"
          data-testid="work-slider"
          class="time-slider"
          :min="WORK_MIN"
          :max="WORK_MAX"
          :step="WORK_STEP"
          :value="currentWorkMinutes"
          :aria-label="$t('focus.workLength')"
          @input="onWorkInput"
        >
        <span class="flex justify-between px-0.5 text-[10px] font-bold text-slate-400">
          <span>{{ durationLabel(WORK_MIN) }}</span>
          <span>{{ durationLabel(45) }}</span>
          <span>{{ durationLabel(90) }}</span>
          <span>{{ durationLabel(WORK_MAX) }}</span>
        </span>
      </span>
    </label>

    <label class="time-slider-group">
      <span class="flex items-center justify-between text-xs font-bold text-slate-500">
        <span>{{ $t('focus.pauseLength') }}</span>
        <strong class="text-slate-700">{{ durationLabel(currentShortPauseMinutes) }}</strong>
      </span>
      <span class="time-slider-wrap time-slider-wrap--pause" :style="{ '--slider-percent': pausePercent + '%' }">
        <span class="time-slider-bubble">{{ durationLabel(currentShortPauseMinutes) }}</span>
        <input
          type="range"
          data-testid="pause-slider"
          class="time-slider"
          :min="PAUSE_MIN"
          :max="PAUSE_MAX"
          :step="PAUSE_STEP"
          :value="currentShortPauseMinutes"
          :aria-label="$t('focus.pauseLength')"
          @input="onPauseInput"
        >
        <span class="flex justify-between px-0.5 text-[10px] font-bold text-slate-400">
          <span>{{ durationLabel(PAUSE_MIN) }}</span>
          <span>{{ durationLabel(15) }}</span>
          <span>{{ durationLabel(PAUSE_MAX) }}</span>
        </span>
      </span>
    </label>
  </div>
</template>

<style scoped>
  .time-slider-group {
    display: flex;
    flex-direction: column;
    gap: 8px;
    width: 100%;
  }

  .time-slider-wrap {
    position: relative;
    display: flex;
    flex-direction: column;
    gap: 5px;
  }

  .time-slider-bubble {
    position: absolute;
    z-index: 2;
    top: -22px;
    left: var(--slider-percent);
    transform: translateX(-50%) translateY(4px);
    border-radius: 999px;
    background: #1f2d3d;
    padding: 3px 8px;
    color: #fff;
    font-size: 10px;
    font-weight: 700;
    line-height: 1.2;
    white-space: nowrap;
    opacity: 0;
    pointer-events: none;
    transition: opacity 140ms ease, transform 140ms ease;
  }

  .time-slider-wrap:hover .time-slider-bubble,
  .time-slider-wrap:focus-within .time-slider-bubble {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }

  .time-slider {
    width: 100%;
    height: 18px;
    appearance: none;
    background: transparent;
    cursor: pointer;
  }

  .time-slider::-webkit-slider-runnable-track {
    height: 6px;
    border-radius: 999px;
    background:
      linear-gradient(to right, #2f7fe0 0%, #2f7fe0 var(--slider-percent), #dce6f1 var(--slider-percent), #dce6f1 100%);
  }

  .time-slider::-moz-range-track {
    height: 6px;
    border-radius: 999px;
    background: #dce6f1;
  }

  .time-slider::-moz-range-progress {
    height: 6px;
    border-radius: 999px;
    background: #2f7fe0;
  }

  .time-slider::-webkit-slider-thumb {
    width: 18px;
    height: 18px;
    margin-top: -6px;
    appearance: none;
    border: 3px solid #fff;
    border-radius: 50%;
    background: #2f7fe0;
    box-shadow: 0 2px 8px rgb(47 127 224 / 35%);
  }

  .time-slider::-moz-range-thumb {
    width: 14px;
    height: 14px;
    border: 3px solid #fff;
    border-radius: 50%;
    background: #2f7fe0;
    box-shadow: 0 2px 8px rgb(47 127 224 / 35%);
  }

  .time-slider-wrap--pause .time-slider::-webkit-slider-runnable-track {
    background:
      linear-gradient(to right, #475569 0%, #475569 var(--slider-percent), #dce6f1 var(--slider-percent), #dce6f1 100%);
  }

  .time-slider-wrap--pause .time-slider::-moz-range-progress {
    background: #475569;
  }

  .time-slider-wrap--pause .time-slider::-webkit-slider-thumb,
  .time-slider-wrap--pause .time-slider::-moz-range-thumb {
    background: #475569;
  }
</style>
