<script setup lang="ts"> // eslint-disable-line vue/multi-word-component-names
import { useI18n } from 'vue-i18n'
import SettingsPanel from '@/components/settings/settingsPanel.vue'
import TodoList from '~~/components/todoList/todoList.vue'
import { useOpenPanels } from '~~/stores/openpanels'
import { useSchedule } from '~~/stores/schedule'
import { useSettings } from '~~/stores/settings'
import GardenPanel from '~/components/garden/gardenPanel.vue'

const openPanels = useOpenPanels()
const settingsStore = useSettings()
const scheduleStore = useSchedule()

const { locale } = useI18n()

/** 把触发按钮在视口里的位置换算成面板内部的 transform-origin。 */
function panelOriginStyle (name: 'settings' | 'garden', maxWidth: number) {
  return computed(() => {
    if (!import.meta.client) {
      return { '--panel-origin-x': '100%', '--panel-origin-y': '0px' }
    }
    const rect = openPanels.panelRect[name]
    const width = Math.min(window.innerWidth, maxWidth)
    const left = window.innerWidth - width
    const x = rect ? rect.left + rect.width / 2 - left : width - 28
    const y = rect ? rect.top + rect.height / 2 : 28
    return {
      '--panel-origin-x': `${Math.round(x)}px`,
      '--panel-origin-y': `${Math.round(y)}px`
    }
  })
}

const settingsOrigin = panelOriginStyle('settings', 640)
const gardenOrigin = panelOriginStyle('garden', 448)

const onKeydown = (event: KeyboardEvent) => {
  if (event.key !== 'Escape') { return }
  if (openPanels.settings || openPanels.garden || openPanels.todo) {
    openPanels.closeAll()
  }
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))

useHead(() => {
  return {
    htmlAttrs: { lang: locale },
    bodyAttrs: {
      class: computed(() => settingsStore.visuals.darkMode ? 'dark' : '')
    },
    link: [{
      rel: "manifest",
      href: "/app_manifest.json"
    }]
  }
})
</script>

<template>
  <div class="relative w-full h-full">
    <Transition
      enter-from-class="opacity-0"
      enter-active-class="transition duration-200"
      leave-to-class="opacity-0"
      leave-active-class="transition duration-200"
    >
      <button
        v-if="openPanels.settings || openPanels.garden || openPanels.todo"
        type="button"
        data-testid="aux-panel-overlay"
        class="fixed inset-0 z-[96] cursor-default bg-slate-900/25 backdrop-blur-[1px]"
        :aria-label="$t('settings.buttons.close')"
        @click="openPanels.closeAll()"
      />
    </Transition>
    <Transition
      enter-from-class="aux-panel-enter-from"
      enter-active-class="aux-panel-enter-active"
      leave-to-class="aux-panel-leave-to"
      leave-active-class="aux-panel-leave-active"
    >
      <SettingsPanel
        v-show="openPanels.settings"
        class="right-0 aux-panel-surface"
        :style="settingsOrigin"
        @click.stop
      />
    </Transition>
    <transition enter-from-class="translate-y-full" enter-active-class="duration-300 ease-out" leave-to-class="translate-y-full" leave-active-class="duration-150 ease-in">
      <TodoList v-if="settingsStore.tasks.enabled && openPanels.todo" class="fixed bottom-0 z-[97] w-full md:max-w-lg transition-all rounded-t-xl md:right-4 md:pb-8" :editing="[0].includes(scheduleStore.timerState)" @hide="openPanels.todo = false" />
    </transition>
    <Transition
      enter-from-class="aux-panel-enter-from"
      enter-active-class="aux-panel-enter-active"
      leave-to-class="aux-panel-leave-to"
      leave-active-class="aux-panel-leave-active"
    >
      <GardenPanel
        v-show="openPanels.garden"
        class="aux-panel-surface"
        :style="gardenOrigin"
        @click.stop
      />
    </Transition>
    <slot />
  </div>
</template>

<style>
/* stylelint-disable-next-line selector-id-pattern */
html, body, #__nuxt {
  height: 100%;
}

.aux-panel-surface {
  clip-path: circle(150vmax at var(--panel-origin-x, 100%) var(--panel-origin-y, 0px));
}

.aux-panel-enter-from,
.aux-panel-leave-to {
  opacity: 0;
  clip-path: circle(0px at var(--panel-origin-x, 100%) var(--panel-origin-y, 0px));
}

.aux-panel-enter-active,
.aux-panel-leave-active {
  transition:
    clip-path 320ms cubic-bezier(0.22, 1, 0.36, 1),
    opacity 180ms ease;
}
</style>
