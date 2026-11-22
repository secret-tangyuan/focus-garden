<script setup lang="ts">
import { IconPlayerPlay, IconPlayerPause, IconPlayerStop, IconPlayerTrackNext } from '@tabler/icons-vue'
import { useI18n } from 'vue-i18n'
import { ButtonImportance, ButtonTheme } from '~~/components/base/types/button'
import CButton from '~~/components/base/uiButton.vue'
import { TimerState, useSchedule } from '~~/stores/schedule'
import { useFocusMode } from '~~/stores/focusMode'
import { useHistory } from '~~/stores/history'
import { useIsland } from '~~/stores/island'

const scheduleStore = useSchedule()
const focusMode = useFocusMode()
const history = useHistory()
const island = useIsland()
const { t } = useI18n()

const reset = () => {
  focusMode.exitImmersive()
  if (scheduleStore.timerState !== TimerState.COMPLETED && scheduleStore.getSchedule[0].timeElapsed > scheduleStore.getSchedule[0].length) {
    scheduleStore.timerState = TimerState.COMPLETED
  } else {
    scheduleStore.timerState = TimerState.STOPPED
  }
  island.show({
    title: String(t('focus.notice.resetTitle')),
    detail: String(t('focus.notice.resetBody')),
    tone: 'info'
  })
}

const playPause = async () => {
  // 暂停 / 继续
  if (scheduleStore.timerState === TimerState.RUNNING) {
    scheduleStore.timerState = TimerState.PAUSED
    island.show({
      title: String(t('focus.notice.pausedTitle')),
      detail: String(t('focus.notice.pausedBody')),
      tone: 'warning'
    })
    return
  }

  // 开始专注：先计时，再请求全屏（请求失败也不影响计时）
  history.recordLogin()
  const startingNewSection = scheduleStore.timerState !== TimerState.PAUSED
  scheduleStore.timerState = TimerState.RUNNING
  if (!startingNewSection) {
    island.show({
      title: String(t('focus.notice.resumedTitle')),
      detail: String(t('focus.notice.resumedBody')),
      tone: 'success'
    })
  }
  if (startingNewSection && scheduleStore.currentSectionType === 'work') {
    focusMode.enterImmersive()
  }

  if (focusMode.enabled && !focusMode.isFullscreen) {
    focusMode.entered = true
    focusMode.requestFullscreen()
  }
}

const advance = () => {
  focusMode.exitImmersive()
  scheduleStore.timerState = TimerState.STOPPED
  scheduleStore.advance()
}
</script>

<template>
  <div class="flex items-center justify-center gap-5 md:gap-8">
    <CButton
      circle
      inner-class="p-5"
      :theme="ButtonTheme.Secondary"
      :importance="ButtonImportance.Filled"
      class="h-16 transition"
      :class="{ 'scale-0 opacity-0 pointer-events-none' : !scheduleStore.isRunning }"
      :aria-label="$t('controls.stop')"
      @click="reset"
    >
      <IconPlayerStop :size="24" />
    </CButton>

    <CButton
      :aria-label="$t('controls.play')"
      inner-class="p-6 px-8 transition"
      bg-class="rounded-full"
      class="h-20 w-28"
      :theme="ButtonTheme.NeutralDark"
      :importance="ButtonImportance.Filled"
      @click="playPause"
    >
      <IconPlayerPlay v-if="scheduleStore.timerState !== TimerState.RUNNING" :size="28" />
      <IconPlayerPause v-else :size="28" />
    </CButton>

    <CButton
      :aria-label="$t('controls.advance')"
      circle
      inner-class="p-5"
      :theme="ButtonTheme.Secondary"
      :importance="ButtonImportance.Filled"
      class="h-16 transition"
      :class="{ 'scale-0 opacity-0 pointer-events-none' : scheduleStore.timerState === TimerState.RUNNING }"
      @click="advance()"
    >
      <IconPlayerTrackNext :size="24" />
    </CButton>
  </div>
</template>
