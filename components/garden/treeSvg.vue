<script setup lang="ts">
import { computed } from 'vue'
import { TreeSpecies, type GrowthStage } from '~~/stores/garden'

const props = withDefaults(defineProps<{
  species: TreeSpecies
  stage: GrowthStage
  /** 高度（px） */
  size?: number
}>(), {
  size: 56
})

/** 每个阶段的树高比例 */
const stageScale = [0.62, 0.8, 0.92, 1]

const trunkHeight = computed(() => 10 * stageScale[props.stage])

const canopyColor = computed(() => {
  if (props.species === TreeSpecies.Cherry) { return '#f7b7cd' }
  if (props.species === TreeSpecies.Pine) { return '#3f7f6b' }
  return '#4f9d69'
})

const canopyColorDark = computed(() => {
  if (props.species === TreeSpecies.Cherry) { return '#e79ab6' }
  if (props.species === TreeSpecies.Pine) { return '#336653' }
  return '#42855c'
})
</script>

<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 100 100"
    fill="none"
    aria-hidden="true"
  >
    <g :transform="'translate(50 100) scale(' + stageScale[stage] + ') translate(-50 -100)'">
      <!-- 树干 -->
      <path d="M46 100 L46 58 Q46 52 50 52 Q54 52 54 58 L54 100 Z" fill="#a4714b" />

      <template v-if="species === TreeSpecies.Pine">
        <path d="M50 6 L74 40 L26 40 Z" :fill="canopyColor" />
        <path d="M50 26 L80 62 L20 62 Z" :fill="canopyColorDark" />
        <path d="M50 46 L86 82 L14 82 Z" :fill="canopyColor" />
      </template>

      <template v-else-if="species === TreeSpecies.Cherry">
        <circle cx="50" cy="40" r="26" :fill="canopyColor" />
        <circle cx="32" cy="52" r="16" :fill="canopyColorDark" />
        <circle cx="68" cy="52" r="16" :fill="canopyColorDark" />
        <circle cx="42" cy="32" r="5" fill="#fff1f6" />
        <circle cx="60" cy="40" r="4" fill="#fff1f6" />
        <circle cx="52" cy="56" r="4" fill="#fff1f6" />
      </template>

      <template v-else>
        <circle cx="50" cy="40" r="24" :fill="canopyColor" />
        <circle cx="31" cy="52" r="16" :fill="canopyColorDark" />
        <circle cx="69" cy="52" r="16" :fill="canopyColorDark" />
        <circle cx="50" cy="24" r="12" :fill="canopyColor" />
      </template>
    </g>
  </svg>
</template>
