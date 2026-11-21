<script setup lang="ts">
import { TimerState, useSchedule } from '~~/stores/schedule'

const scheduleStore = useSchedule()
const running = computed(() => scheduleStore.getCurrentTimerState === TimerState.RUNNING)
const emit = defineEmits<{(event: 'tick', timeString: string): void }>()

interface Part {
  id: string
  colon: boolean
  text: string
  /** 小时 / 分钟 / 秒 */
  role: 'hours' | 'minutes' | 'seconds' | null
}

const timeLeftStructured = computed(() => {
  const sLeft = Math.abs(Math.round((scheduleStore.getCurrentItem.length - scheduleStore.getCurrentItem.timeElapsed) / 1000))
  const hours = Math.floor(sLeft / (60 * 60))
  const minutes = Math.floor((sLeft % (60 * 60)) / 60)
  const seconds = Math.floor(sLeft % 60)

  const timeStructured = { hours, minutes, seconds }
  const displayKeys = (Object.keys(timeStructured) as Array<keyof typeof timeStructured>)
    .filter(value => value !== 'hours' || hours > 0)

  const completed = scheduleStore.getCurrentItem.timeElapsed > scheduleStore.getCurrentItem.length
    && [hours, minutes, seconds].some(num => num > 0)

  // 分钟和秒之间用冒号连接，时分之间也用冒号
  const parts: Part[] = []
  for (const key of displayKeys) {
    if (parts.length > 0) {
      parts.push({ id: 'colon-' + key, colon: true, text: ':', role: null })
    }
    parts.push({ id: key, colon: false, text: timeStructured[key].toString().padStart(2, '0'), role: key })
  }

  emit(
    'tick',
    (completed ? '+' : '') + displayKeys
      .map(key => timeStructured[key].toString().padStart(2, '0'))
      .join(':')
  )

  return { parts, completed }
})
</script>

<template>
  <div
    :class="['md:text-[13rem] text-[8rem] leading-none timer-display relative', { 'active': running }]"
  >
    <transition-group
      name="transition-traditional"
      enter-from-class="translate-y-4 opacity-0 md:translate-y-0 md:translate-x-4"
      enter-active-class="duration-500"
      enter-to-class=""
      leave-class=""
      leave-active-class="absolute duration-300"
      leave-to-class="opacity-0 md:translate-x-8"
      move-class="duration-500"
      class="relative flex flex-row items-center transition isolate"
      tag="div"
    >
      <div v-if="timeLeftStructured.completed" class="pr-1 text-[.7em] font-bold">
        +
      </div>
      <div
        v-for="part in timeLeftStructured.parts"
        :key="part.id"
        class="flex flex-row items-center transition"
        :class="{ 'font-bold': part.role === 'minutes' || part.colon }"
      >
        <template v-if="part.colon">
          <span class="px-[0.06em] leading-none">:</span>
        </template>
        <template v-else>
          <span
            v-for="(char, idx) in part.text"
            :key="idx"
            class="w-[1ch]"
            v-text="char"
          />
        </template>
      </div>
    </transition-group>
  </div>
</template>
