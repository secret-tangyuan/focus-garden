<script setup>
import { IconSettings, IconChecklist, IconTrees, IconLogin, IconMaximizeOff, IconArrowsMinimize } from '@tabler/icons-vue'
import { ButtonImportance, ButtonTheme } from './base/types/button'
import CButton from '~~/components/base/uiButton.vue'
import ScheduleView from '@/components/schedule/scheduleDisplay.vue'
import { useOpenPanels } from '@/stores/openpanels'
import { TimerState, useSchedule } from '~~/stores/schedule'
import { useSettings } from '~~/stores/settings'
import { useAuth } from '~~/stores/auth'
import { useFocusMode } from '~~/stores/focusMode'

const openPanels = useOpenPanels()
const auth = useAuth()
const scheduleStore = useSchedule()
const focusMode = useFocusMode()

/** 只有在专注中（计时在跑或已进全屏）才显示「暂停并退出」 */
const showExitFocus = computed(() =>
  scheduleStore.timerState === TimerState.RUNNING || focusMode.isFullscreen
)
const canEnterImmersive = computed(() =>
  scheduleStore.timerState === TimerState.RUNNING &&
  scheduleStore.currentSectionType === 'work' &&
  !focusMode.immersive
)

/** 暂停计时并退出全屏：直接执行，不做二次确认 */
const pauseAndExit = async () => {
  if (scheduleStore.timerState === TimerState.RUNNING) {
    scheduleStore.timerState = TimerState.PAUSED
  }
  // 不标记成「因退出全屏而暂停」：回来后不要自动继续
  focusMode.clearPausedByExit()
  focusMode.exitImmersive()
  await focusMode.exitFullscreen()
}
const { requestAccess } = usePanelAccess()
const settingsStore = useSettings()
</script>

<template>
  <div class="flex flex-row items-center w-full gap-2 px-4 my-1 isolate h-14">
    <div v-show="settingsStore.schedule.visibility.enabled" class="flex-shrink-0 h-10 px-2 py-2 rounded-full bg-surface-dark dark:ring-1 ring-inset dark:ring-surface-ondark dark:ring-opacity-20 overflow-hidden">
      <ClientOnly>
        <ScheduleView />
      </ClientOnly>
    </div>
    <div v-show="settingsStore.schedule.visibility.enabled && settingsStore.schedule.visibility.showSectionType" class="flex-shrink overflow-hidden text-lg whitespace-pre select-none text-ellipsis text-surface-onlight dark:text-surface-ondark" v-text="$t('section.' + scheduleStore.getCurrentItem.type).toLowerCase()" />
    <div class="flex-grow" />
    <CButton
      v-show="settingsStore.tasks.enabled"
      circle
      :theme="openPanels.todo ? ButtonTheme.Primary : ButtonTheme.Neutral"
      :importance="ButtonImportance.Tonal"
      class="transition rounded-full h-11"
      no-content-theme
      no-padding
      inner-class="p-1"
      :aria-label="$t('appbar.todo')"
      @click="openPanels.todo = !openPanels.todo"
    >
      <IconChecklist size="24" class="inline-block" />
    </CButton>
    <button
      v-if="showExitFocus"
      class="flex shrink-0 items-center gap-1.5 rounded-full bg-white/75 px-3 py-2 text-xs font-bold text-slate-600 shadow-sm transition hover:bg-white hover:text-slate-900"
      :aria-label="$t('focus.exit.label')"
      @click="pauseAndExit"
    >
      <IconMaximizeOff :size="16" />
      <span class="hidden md:inline">{{ $t('focus.exit.text') }}</span>
    </button>
    <CButton
      v-if="canEnterImmersive"
      circle
      :theme="ButtonTheme.Neutral"
      :importance="ButtonImportance.Tonal"
      class="transition rounded-full h-11"
      no-content-theme
      no-padding
      inner-class="p-1"
      :aria-label="$t('focus.immersive.enter')"
      @click="focusMode.enterImmersive()"
    >
      <IconArrowsMinimize size="22" class="inline-block" />
    </CButton>
    <CButton
      v-if="auth.identityReady"
      circle
      :theme="ButtonTheme.Neutral"
      :importance="ButtonImportance.Tonal"
      class="transition rounded-full h-11"
      no-content-theme
      no-padding
      inner-class="p-1"
      :aria-label="$t('appbar.login')"
      @click="requestAccess('login', $event.currentTarget.getBoundingClientRect())"
    >
      <span v-if="auth.authenticated" class="text-xs font-bold">{{ auth.displayName }}</span>
      <IconLogin v-else size="24" class="inline-block" />
    </CButton>
    <CButton
      circle
      :theme="openPanels.garden ? ButtonTheme.Primary : ButtonTheme.Neutral"
      :importance="ButtonImportance.Tonal"
      class="transition rounded-full h-11"
      no-content-theme
      no-padding
      inner-class="p-1"
      :aria-label="$t('appbar.garden')"
      @click="requestAccess('garden', $event.currentTarget.getBoundingClientRect())"
    >
      <IconTrees size="24" class="inline-block" />
    </CButton>
    <CButton
      circle
      :aria-label="$t('appbar.settings')"
      :importance="ButtonImportance.Filled"
      :theme="ButtonTheme.Neutral"
      class="h-11"
      no-content-theme
      no-padding
      inner-class="p-1"
      @click="requestAccess('settings', $event.currentTarget.getBoundingClientRect())"
    >
      <IconSettings size="24" class="inline-block" />
    </CButton>
  </div>
</template>
