<script setup lang="ts">
import { defineAsyncComponent } from 'vue'
import { useI18n } from 'vue-i18n'
import { useHead } from '#imports'
import { useSchedule } from '~~/stores/schedule'
import { useSettings } from '~~/stores/settings'
import { useAuth } from '~~/stores/auth'

import { useTicker } from '~~/components/ticker'
import { useWeb } from '~~/platforms/web'
import { useMobile } from '~~/platforms/mobile'

import TimerSwitch from '@/components/timer/display/_timerSwitch.vue'
import TimerProgress from '@/components/timer/timerProgress.vue'
import TimerControls from '@/components/timer/controls/controlsNew.vue'
import { AppPlatform } from '~~/platforms/platforms'

import { useMobileSettings } from '~~/stores/platforms/mobileSettings'

import Layout from '~/layouts/timer.vue'
import FullscreenGuard from '~/components/focus/fullscreenGuard.vue'
import PlantToast from '~/components/garden/plantToast.vue'
import StartGate from '~/components/focus/startGate.vue'
import QuickPresets from '~/components/focus/quickPresets.vue'
import DistractionTip from '~/components/focus/distractionTip.vue'
import LoginPanel from '~/components/focus/loginPanel.vue'

// components
const AppBar = defineAsyncComponent(() => import('@/components/appBar.vue'))

const settingsStore = useSettings()
const mobileSettingsStore = useMobileSettings()
const scheduleStore = useSchedule()

const runtimeConfig = useRuntimeConfig()

const { t } = useI18n()

const iconSvg = computed(() => `data:image/svg+xml,
<svg
  width="32"
  height="32"
  viewBox="0 0 32 32"
  fill="none"
  style="color: ${scheduleStore.currentScheduleColour};"
  xmlns="http://www.w3.org/2000/svg"
>
<circle cx="16" cy="16" r="14" fill="currentColor" /></svg>`)

useHead({
  link: [
    {
      rel: 'manifest',
      href: '/app_manifest.json'
    },
    {
      rel: 'apple-touch-icon',
      href: '/icons/icon-apple-192.png'
    }
  ],
  meta: [
    { name: 'theme-color', content: '#bbddff' }
  ]
})

if (!import.meta.server) {
  useHead({
    link: [
      {
        rel: 'icon',
        type: 'image/svg+xml',
        href: iconSvg
      }
    ]
  })
}

onMounted(() => {
  // 读取统一身份会话（精简登录用）
  const auth = useAuth()
  auth.fetchSession()

  // 从后台切回前台时，会话快过期就自动续签（免密）
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
      void auth.renewIfStale()
    }
  })

  if (typeof window !== 'undefined') {
    if ('serviceWorker' in navigator) {
      const registerSw = () => {
        console.debug('Registering service worker at /serviceworker.js')
        navigator.serviceWorker.register('/serviceworker.js')
      }

      if (document.readyState === 'complete') {
        registerSw()
      } else {
        window.addEventListener('load', registerSw)
      }
    }
  }
})

useTicker()

// Load appropriate platform module based on runtime config
if (runtimeConfig.public.PLATFORM === AppPlatform.web) {
  useWeb()
} else if (runtimeConfig.public.PLATFORM === AppPlatform.mobile) {
  useMobile()
}

const state = reactive({
  timeString: ''
})

const remainingTimeString = computed(() => {
  if (scheduleStore.getCurrentTimerState === 3) {
    return settingsStore.pageTitle.useTickEmoji ? '✔' : t('ready').toLowerCase()
  }

  return state.timeString
})

const pageTitle = computed(() => {
  return scheduleStore.getCurrentItem
    ? t('section.' + scheduleStore.getCurrentItem.type).toLowerCase()
    : 'Pomodoro'
})

const progressBarSchedules = computed(() => {
  const numSchedules = settingsStore.performance.showProgressBar ? 2 : 1
  return scheduleStore.getSchedule.slice(0, numSchedules)
})
</script>

<template>
  <Layout>
    <section class="h-full overflow-hidden duration-300 ease-in dark:text-gray-50">
      <Title>{{ (remainingTimeString ? `(${remainingTimeString}) ` : '') + pageTitle }}</Title>
      <!-- 背景：纯色 + 格子 -->
      <div class="absolute w-full h-full bg-[#f7fafc] dark:bg-[#151b23] grid-bg" />
      <!-- Progress bar -->
      <TransitionGroup name="progress-transition" :duration="1000">
        <TimerProgress
          v-for="(scheduleItem, index) in progressBarSchedules"
          :key="scheduleItem.id"
          :colour="scheduleStore.getScheduleColour[index]"
          :schedule-entry-id="scheduleItem.id"
          :background="index === 0"
          :time-elapsed="scheduleStore.getCurrentItem.timeElapsed"
          :time-original="scheduleStore.getCurrentItem.length"
        />
      </TransitionGroup>
      <div
        class="relative flex flex-col items-center justify-center w-full h-full isolate"
        :style="{
          'padding-top': `${mobileSettingsStore.padding.top}px`,
          'padding-bottom': `${mobileSettingsStore.padding.bottom}px`
        }"
      >
        <AppBar />
        <TimerSwitch
          key="timerswitch"
          :time-elapsed="scheduleStore.getCurrentItem.timeElapsed"
          :time-original="scheduleStore.getCurrentItem.length"
          :timer-state="scheduleStore.timerState"
          :timer-widget="settingsStore.currentTimer"
          class="flex-grow"
          @tick="state.timeString = $event"
        />
        <QuickPresets class="mb-6" />
        <TimerControls class="mb-8" />
      </div>
      <FullscreenGuard />
      <PlantToast />
      <StartGate />
      <DistractionTip />
      <LoginPanel />
    </section>
  </Layout>
</template>

<style lang="scss" scoped>
.timer-background {
  transition: 300ms ease-in;
  transition-property: background-color;
  position: relative;
  height: 100%;
}

.schedule-transition-enter-active,
.schedule-transition-leave-active {
  transition: transform 300ms ease-out, opacity 200ms ease-out;
}

.schedule-transition-enter,
.schedule-transition-leave-to {
  transform: translateY(-20px);
  opacity: 0;
}

.progress-transition-leave-to {
  @apply transform-gpu translate-x-0;
}

.progress-transition-enter {
  @apply transform-gpu -translate-x-full;
}
</style>

<style>
body {
  overscroll-behavior-y: contain;
}

/* 纯色背景 + 格子 */
.grid-bg {
  background-image:
    linear-gradient(to right, rgba(31, 45, 61, 0.045) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(31, 45, 61, 0.045) 1px, transparent 1px);
  background-size: 44px 44px;
}

/* 计时进度色块：半透明，露出格子底 */
.timer-progress {
  opacity: 0.55;
}

.dark .grid-bg {
  background-image:
    linear-gradient(to right, rgba(187, 221, 255, 0.05) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(187, 221, 255, 0.05) 1px, transparent 1px);
}
</style>
