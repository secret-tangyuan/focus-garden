<script setup lang="ts">
/**
 * 植物美术渲染器（12 物种 × 5 形态 + 枯萎态）
 *
 * 移植自 FocusGrove（MIT License, Copyright (c) 2026 FocusGrove contributors）
 * https://github.com/haminyovanantonyfk-netizen/focus-grove
 * 原实现：app.js 中的 `SPECIES` 表 + `treeSVG()`（原生 JS 字符串模板）
 *
 * 本文件为其 Vue 3 改写版。MIT 许可要求保留原版权与许可声明：
 * 见仓库根目录 licenses/focus-grove-LICENSE 与 NOTICE.md。
 */
import { computed } from 'vue'
import { PLANT_SPECIES, type PlantSpecies, type GrowthStage } from '~~/stores/garden'

const props = withDefaults(defineProps<{
  species: PlantSpecies
  stage: GrowthStage
  /** 高度（px） */
  size?: number
  /** 枯萎态（灰化） */
  dead?: boolean
}>(), {
  size: 56,
  dead: false
})

const info = computed(() => PLANT_SPECIES[props.species] ?? PLANT_SPECIES.maple)

const c1 = computed(() => props.dead ? '#9ca3af' : info.value.c1)
const c2 = computed(() => props.dead ? '#6b7280' : info.value.c2)
const trunk = computed(() => props.dead ? '#78716c' : '#92400e')
const shape = computed(() => info.value.shape)

/** 上游的阶段尺寸表：stage 0/1 单独画，2~4 用这两个数控制高度与冠幅 */
const H = [0, 0, 86, 64, 40]
const R = [0, 0, 26, 40, 54]
const h = computed(() => H[props.stage] ?? 40)
const r = computed(() => R[props.stage] ?? 54)

/** 花 / 竹 / 仙人掌自带茎干，不再画通用树干 */
const hasTrunk = computed(() => !['flower', 'bamboo', 'cactus'].includes(shape.value))
</script>

<template>
  <svg
    :width="size"
    :height="size * 1.2"
    viewBox="0 0 150 180"
    fill="none"
    aria-hidden="true"
  >
    <!-- 形态 0：种子冒芽 -->
    <template v-if="stage === 0">
      <ellipse cx="75" cy="158" rx="34" ry="9" fill="#bbf7d0" />
      <ellipse cx="75" cy="150" rx="13" ry="9" :fill="trunk" />
      <path d="M75 148 q4 -14 12 -18" stroke="#16a34a" stroke-width="4" fill="none" stroke-linecap="round" />
    </template>

    <!-- 形态 1：幼苗 -->
    <template v-else-if="stage === 1">
      <ellipse cx="75" cy="162" rx="38" ry="9" fill="#bbf7d0" />
      <path d="M75 160 L75 118" :stroke="trunk" stroke-width="7" stroke-linecap="round" />
      <ellipse cx="62" cy="112" rx="15" ry="9" :fill="c1" transform="rotate(-25 62 112)" />
      <ellipse cx="89" cy="104" rx="15" ry="9" :fill="c2" transform="rotate(25 89 104)" />
    </template>

    <!-- 形态 2~4 -->
    <template v-else>
      <ellipse cx="75" cy="166" rx="44" ry="9" fill="#bbf7d0" />

      <path
        v-if="hasTrunk"
        :d="`M75 165 L75 ${h + 30}`"
        :stroke="trunk"
        stroke-width="9"
        stroke-linecap="round"
      />

      <template v-if="shape === 'pine'">
        <path :d="`M75 ${h - 38} L${75 + r} ${h + 42} L${75 - r} ${h + 42} Z`" :fill="c1" />
        <path :d="`M75 ${h - 14} L${75 + r + 8} ${h + 66} L${75 - r - 8} ${h + 66} Z`" :fill="c2" />
      </template>

      <template v-else-if="shape === 'palm'">
        <path
          :d="`M75 ${h} q-44 -26 -58 4 M75 ${h} q-20 -38 8 -46 M75 ${h} q30 -30 48 -6 M75 ${h} q44 -8 44 18`"
          :stroke="c1"
          stroke-width="9"
          fill="none"
          stroke-linecap="round"
        />
      </template>

      <template v-else-if="shape === 'bamboo'">
        <path
          :d="`M58 165 L58 ${h + 10} M75 165 L75 ${h - 8} M92 165 L92 ${h + 16}`"
          :stroke="c1"
          stroke-width="9"
          stroke-linecap="round"
        />
        <path :d="`M58 ${h + 34} h34 M75 ${h + 10} h30`" :stroke="c2" stroke-width="5" />
      </template>

      <template v-else-if="shape === 'cactus'">
        <path
          :d="`M75 165 L75 ${h + 6} M75 ${h + 52} q-24 0 -24 -22 M99 ${h + 66} q24 0 24 -26`"
          :stroke="c1"
          stroke-width="13"
          fill="none"
          stroke-linecap="round"
        />
      </template>

      <template v-else-if="shape === 'flower'">
        <circle cx="75" :cy="h + 16" :r="r * 0.55" :fill="c2" />
        <circle cx="75" :cy="h + 16" :r="r * 0.28" :fill="c1" />
        <path :d="`M75 165 L75 ${h + 24}`" stroke="#16a34a" stroke-width="7" stroke-linecap="round" />
      </template>

      <template v-else-if="shape === 'willow'">
        <circle cx="75" :cy="h + 14" :r="r * 0.8" :fill="c1" />
        <path
          :d="`M45 ${h + 24} q-4 34 6 52 M75 ${h + 30} q0 36 4 54 M105 ${h + 24} q4 34 -6 52`"
          :stroke="c2"
          stroke-width="6"
          fill="none"
          stroke-linecap="round"
        />
      </template>

      <template v-else>
        <circle cx="75" :cy="h + 18" :r="r" :fill="c1" />
        <circle :cx="75 - r + 8" :cy="h + 38" :r="r * 0.68" :fill="c2" />
        <circle :cx="75 + r - 8" :cy="h + 38" :r="r * 0.68" :fill="c1" />
      </template>
    </template>
  </svg>
</template>
