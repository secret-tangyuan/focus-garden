<script setup lang="ts">
import { IconClock } from '@tabler/icons-vue'
import { useI18n } from 'vue-i18n'
import Button from '~~/components/base/uiButton.vue'
import { ButtonImportance } from '~~/components/base/types/button'
import { useIsland } from '~~/stores/island'

const island = useIsland()
const { t } = useI18n()

/** 是否显示实时时钟 */
const visible = ref(false)
const now = ref(new Date())
let timer: ReturnType<typeof setInterval> | null = null

const pad = (value: number) => String(value).padStart(2, '0')

const dateText = computed(() => {
  const d = now.value
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
})

const timeText = computed(() => {
  const d = now.value
  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
})

const zoneText = computed(() => {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone
  } catch (err) {
    return ''
  }
})

const startClock = () => {
  now.value = new Date()
  if (timer) { clearInterval(timer) }
  timer = setInterval(() => { now.value = new Date() }, 1000)
}

const stopClock = () => {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

const toggle = () => {
  visible.value = !visible.value
  if (visible.value) {
    startClock()
    island.show({
      title: String(t('settings.clock.shown')),
      detail: `${dateText.value} ${timeText.value}`,
      tone: 'info',
      duration: 3000,
      focus: 'defer'
    })
  } else {
    stopClock()
    island.show({
      title: String(t('settings.clock.hidden')),
      tone: 'info',
      duration: 2400
    })
  }
}

onBeforeUnmount(stopClock)
</script>

<template>
  <div class="flex flex-col gap-2">
    <div class="flex flex-row items-center gap-4">
      <div class="flex-grow select-none">
        <div v-text="$t('settings.clock.title')" />
        <div class="text-sm opacity-80" v-text="$t('settings.clock.description')" />
      </div>
      <div class="flex-shrink-0">
        <Button
          :importance="ButtonImportance.Filled"
          :aria-label="$t('settings.clock.button')"
          data-testid="system-clock-button"
          @click="toggle"
        >
          <span class="flex items-center gap-1.5 text-xs font-bold">
            <IconClock :size="16" />
            <span v-text="visible ? $t('settings.clock.hide') : $t('settings.clock.button')" />
          </span>
        </Button>
      </div>
    </div>

    <div
      v-if="visible"
      class="flex flex-row items-center gap-3 rounded-2xl bg-primary/10 px-4 py-3"
      data-testid="system-clock-value"
    >
      <IconClock :size="20" class="shrink-0 text-primary" />
      <span class="font-mono text-xl font-bold tabular-nums" v-text="timeText" />
      <span class="font-mono text-xs opacity-70" v-text="dateText" />
      <span
        v-if="zoneText"
        class="ml-auto font-mono text-[10px] opacity-50"
        v-text="zoneText"
      />
    </div>
  </div>
</template>
