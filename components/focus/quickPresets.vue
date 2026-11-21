<script setup lang="ts">
import { useSchedule } from '~~/stores/schedule'
import { useSettings } from '~~/stores/settings'

const scheduleStore = useSchedule()
const settingsStore = useSettings()

const workOptions = [15, 25, 45, 60, 90]
const pauseOptions = [5, 10, 15]

const currentWorkMinutes = computed(() => Math.round(settingsStore.schedule.lengths.work / 60000))
const currentShortPauseMinutes = computed(() => Math.round(settingsStore.schedule.lengths.shortpause / 60000))
const currentLongPauseMinutes = computed(() => Math.round(settingsStore.schedule.lengths.longpause / 60000))

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
</script>

<template>
  <div class="flex flex-col items-center gap-2">
    <div class="flex flex-wrap items-center justify-center gap-1.5">
      <span class="mr-1 text-xs font-bold text-slate-400">{{ $t('focus.workLength') }}</span>
      <button
        v-for="minutes in workOptions"
        :key="'w' + minutes"
        class="rounded-full px-3 py-1.5 text-xs font-bold transition"
        :class="currentWorkMinutes === minutes
          ? 'bg-brand text-brand-ink shadow-sm'
          : 'bg-white/70 text-slate-500 hover:bg-white hover:text-slate-700'"
        @click="applyWork(minutes)"
      >
        {{ minutes }} {{ $t('focus.minutes') }}
      </button>
    </div>

    <div class="flex flex-wrap items-center justify-center gap-1.5">
      <span class="mr-1 text-xs font-bold text-slate-400">{{ $t('focus.pauseLength') }}</span>
      <button
        v-for="minutes in pauseOptions"
        :key="'p' + minutes"
        class="rounded-full px-3 py-1.5 text-xs font-bold transition"
        :class="(currentShortPauseMinutes === minutes || currentLongPauseMinutes === minutes)
          ? 'bg-slate-700 text-white shadow-sm'
          : 'bg-white/70 text-slate-500 hover:bg-white hover:text-slate-700'"
        @click="applyPause(minutes)"
      >
        {{ minutes }} {{ $t('focus.minutes') }}
      </button>
    </div>
  </div>
</template>
