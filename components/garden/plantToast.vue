<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { useGarden } from '~~/stores/garden'
import { useIsland } from '~~/stores/island'

const garden = useGarden()
const island = useIsland()
const { t } = useI18n()
const shownAt = ref(0)

watch(() => garden.lastPlantedAt, (value) => {
  if (!value || value === shownAt.value) { return }
  shownAt.value = value
  island.show({
    title: String(t('garden.planted')),
    detail: `+${garden.lastPlantedMinutes} ☀️ · ${t('garden.total')} ${garden.totalMinutes} min`,
    tone: 'garden',
    duration: 3600
  })
})
</script>

<template>
  <span class="hidden" aria-hidden="true" />
</template>
