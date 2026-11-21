<script setup lang="ts">
import { IconMaximize, IconLeaf, IconCheck, IconSquare, IconSettings, IconLogin } from '@tabler/icons-vue'
import { TimerState, useSchedule } from '~~/stores/schedule'
import { useFocusMode } from '~~/stores/focusMode'
import { useSettings } from '~~/stores/settings'
import { useHistory } from '~~/stores/history'
import { useAuth } from '~~/stores/auth'
import QuickPresets from '~/components/focus/quickPresets.vue'

const focusMode = useFocusMode()
const scheduleStore = useSchedule()
const settingsStore = useSettings()
const history = useHistory()
const auth = useAuth()

const { requestAccess } = usePanelAccess()

const visible = computed(() => !focusMode.entered)

const start = () => {
  focusMode.entered = true
  history.recordLogin()
  scheduleStore.timerState = TimerState.RUNNING

  if (settingsStore.focus.fullscreen) {
    focusMode.requestFullscreen()
  }
}

const skip = () => {
  focusMode.entered = true
  history.recordLogin()
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="visible"
      class="fixed inset-0 z-[95] flex flex-col items-center justify-center gap-6 px-6 text-center backdrop-blur-sm"
      style="background-color: rgba(247, 250, 252, 0.97)"
    >
      <!-- 右上角：设置与登录，一进来就能点 -->
      <div class="absolute right-5 top-5 flex items-center gap-2">
        <button
          class="flex items-center gap-1.5 rounded-full bg-white/80 px-3 py-2 text-xs font-bold text-slate-500 shadow-sm transition hover:bg-white hover:text-slate-800"
          :aria-label="$t('appbar.settings')"
          @click="requestAccess('settings', $event.currentTarget.getBoundingClientRect())"
        >
          <IconSettings :size="16" />
          {{ $t('appbar.settings') }}
        </button>
        <button
          class="flex items-center gap-1.5 rounded-full bg-white/80 px-3 py-2 text-xs font-bold text-slate-500 shadow-sm transition hover:bg-white hover:text-slate-800"
          :aria-label="$t('appbar.login')"
          @click="requestAccess('login', $event.currentTarget.getBoundingClientRect())"
        >
          <IconLogin :size="16" />
          {{ auth.authenticated ? auth.displayName : $t('appbar.login') }}
        </button>
      </div>

      <span class="flex h-16 w-16 items-center justify-center rounded-3xl bg-brand/25 text-brand-strong">
        <IconLeaf :size="32" />
      </span>

      <div>
        <h1 class="text-3xl font-bold text-slate-800">{{ $t('focus.gate.title') }}</h1>
        <p class="mt-2 max-w-md text-sm leading-relaxed text-slate-500">{{ $t('focus.gate.subtitle') }}</p>
      </div>

      <QuickPresets />

      <button
        class="flex items-center gap-2 rounded-full bg-brand-strong px-8 py-4 text-lg font-bold text-white shadow-lg transition hover:brightness-110"
        @click="start"
      >
        <IconMaximize v-if="settingsStore.focus.fullscreen" :size="24" />
        <IconLeaf v-else :size="24" />
        {{ settingsStore.focus.fullscreen ? $t('focus.gate.start') : $t('focus.gate.startPlain') }}
      </button>

      <div class="flex flex-col items-center gap-2">
        <button
          class="flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-bold transition"
          :class="settingsStore.focus.fullscreen ? 'bg-brand/25 text-brand-strong' : 'text-slate-400 hover:text-slate-600'"
          @click="settingsStore.focus.fullscreen = !settingsStore.focus.fullscreen"
        >
          <IconCheck v-if="settingsStore.focus.fullscreen" :size="16" />
          <IconSquare v-else :size="16" />
          {{ $t('focus.gate.forceFullscreen') }}
        </button>

        <button
          v-if="settingsStore.focus.fullscreen"
          class="flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-bold transition"
          :class="settingsStore.focus.pauseOnExit ? 'bg-brand/25 text-brand-strong' : 'text-slate-400 hover:text-slate-600'"
          @click="settingsStore.focus.pauseOnExit = !settingsStore.focus.pauseOnExit"
        >
          <IconCheck v-if="settingsStore.focus.pauseOnExit" :size="16" />
          <IconSquare v-else :size="16" />
          {{ $t('focus.gate.pauseOnExit') }}
        </button>
      </div>

      <button class="text-xs text-slate-400 underline-offset-4 transition hover:text-slate-600 hover:underline" @click="skip">
        {{ $t('focus.gate.skip') }}
      </button>
    </div>
  </Teleport>
</template>
