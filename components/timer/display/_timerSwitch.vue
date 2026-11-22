<script setup lang="ts">
import { Section, TimerType } from '~~/stores/settings'
import { TimerState, useSchedule } from '~~/stores/schedule'

import TimerTraditional from '@/components/timer/display/timerTraditional.vue'
import TimerApproximate from '@/components/timer/display/timerApproximate.vue'
import TimerPercentage from '@/components/timer/display/timerPercentage.vue'
import CompleteMarker from '@/components/timer/display/timerComplete.vue'

export interface TimerInfo {
  timeElapsed: number,
  timeOriginal: number,
  timerState: number
}

const scheduleStore = useSchedule()

interface Props {
  timerWidget: TimerType
}

const props = withDefaults(defineProps<Props>(), {
  timerWidget: TimerType.Traditional
})

const running = computed(() => scheduleStore.timerState === TimerState.RUNNING)
/** 专注工作段固定用秒表（时分秒）；休息段才用用户选择的样式。 */
const forceSeconds = computed(() =>
  scheduleStore.currentSectionType === Section.work &&
  scheduleStore.getCurrentTimerState !== TimerState.COMPLETED
)
</script>

<template>
  <div class="relative grid text-black transition-opacity duration-500 select-none place-items-center dark:text-gray-100" :class="[{ 'opacity-70': !running, 'opacity-100': running }]">
    <Transition name="timer-switch" mode="out-in">
      <CompleteMarker v-if="scheduleStore.getCurrentTimerState === TimerState.COMPLETED" :key="'complete'" />
      <TimerTraditional
        v-else-if="forceSeconds || props.timerWidget === TimerType.Traditional"
        :key="'traditional'"
        @tick="$emit('tick', $event)"
      />
      <TimerApproximate
        v-else-if="props.timerWidget === 'approximate'"
        :key="'approximate'"
        @tick="$emit('tick', $event)"
      />
      <TimerPercentage
        v-else-if="props.timerWidget === 'percentage'"
        :key="'percentage'"
        @tick="$emit('tick', $event)"
      />
    </Transition>
  </div>
</template>

<style lang="scss" scoped>
.timer-switch-enter-active,
.timer-switch-leave-active {
  transition: opacity 0.5s ease-out;
}

.timer-switch-enter,
.timer-switch-leave-to {
  opacity: 0 !important;
}
</style>
