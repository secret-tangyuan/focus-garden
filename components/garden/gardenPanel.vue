<script setup lang="ts">
import {
  IconX, IconTrees, IconClock, IconFlame, IconTrash, IconList, IconLogin, IconCheck,
  IconSun, IconDroplet, IconPlant2, IconLock, IconChevronRight, IconLeaf
} from '@tabler/icons-vue'
import {
  PLANT_SPECIES, SPECIES_ORDER, PLANT_COST, MAX_STAGE, WATER_LIMIT,
  useGarden, type PlantSpecies
} from '~~/stores/garden'
import { useHistory } from '~~/stores/history'
import { useOpenPanels } from '~~/stores/openpanels'
import { useI18n } from 'vue-i18n'
import PlantSvg from '~~/components/garden/plantSvg.vue'

const garden = useGarden()
const history = useHistory()
const openPanels = useOpenPanels()
const i18n = useI18n()

const tab = ref<'forest' | 'garden' | 'records'>('forest')
/** 当前选中的树 */
const selectedId = ref<number | null>(null)
/** 手动种树时选中的物种 */
const pickedSpecies = ref<PlantSpecies>('maple')
/** 首次引导是否已关闭 */
const guideClosed = ref(false)

const GUIDE_KEY = 'focus-garden-guide-closed'

const selected = computed(() => garden.trees.find(tree => tree.id === selectedId.value) ?? null)
const locked = computed(() => SPECIES_ORDER.filter(id => !garden.unlocked.includes(id)))
const shown = computed(() => garden.forest.slice(0, 60))
const waterCost = computed(() => selected.value ? garden.waterCostOf(selected.value) : 0)
const canWater = computed(() => !!selected.value && garden.canWater(selected.value) && garden.sunlight >= waterCost.value)
const canPlant = computed(() => garden.sunlight >= PLANT_COST && garden.treeCount < garden.plotCapacity)
const canExpand = computed(() => garden.nextExpandCost !== null && garden.sunlight >= garden.nextExpandCost)

/** 状态行：阳光不够时说明还差多少（把灰按钮变成进度而不是故障） */
const hint = computed(() => {
  if (selected.value) {
    const cost = waterCost.value
    if (garden.sunlight < cost) { return i18n.t('garden.hintShort', { n: cost - garden.sunlight }) }
    return ''
  }
  if (garden.sunlight < PLANT_COST) { return i18n.t('garden.hintShort', { n: PLANT_COST - garden.sunlight }) }
  return ''
})

const speciesName = (id: PlantSpecies) => String(i18n.t(`garden.species.${id}`))

onMounted(() => {
  try {
    guideClosed.value = localStorage.getItem(GUIDE_KEY) === '1'
  } catch (err) {
    guideClosed.value = false
  }
  // 检查有没有因为太久没打理而枯萎的树
  garden.checkWither()
})

const closeGuide = () => {
  guideClosed.value = true
  try { localStorage.setItem(GUIDE_KEY, '1') } catch (err) { /* 忽略 */ }
}

const select = (id: number) => {
  selectedId.value = selectedId.value === id ? null : id
}

const waterSelected = () => {
  if (selected.value) { garden.waterTree(selected.value.id) }
}

const plantPicked = () => {
  garden.plantManual(pickedSpecies.value)
}

const unlock = (id: PlantSpecies) => {
  garden.unlockSpecies(id)
}

const expand = () => {
  garden.expandGarden()
}

const confirmClear = ref(false)
const clear = () => {
  if (!confirmClear.value) {
    confirmClear.value = true
    setTimeout(() => { confirmClear.value = false }, 4000)
    return
  }
  garden.clearForest()
  history.clearHistory()
  selectedId.value = null
  confirmClear.value = false
}

const formatTime = (timestamp: number) => {
  const date = new Date(timestamp)
  return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

const formatDay = (timestamp: number) => {
  const date = new Date(timestamp)
  const today = new Date().toDateString()
  const yesterday = new Date(Date.now() - 86400000).toDateString()
  if (date.toDateString() === today) { return i18n.t('garden.today') }
  if (date.toDateString() === yesterday) { return i18n.t('garden.yesterday') }
  return `${date.getMonth() + 1}月${date.getDate()}日`
}

const maxWeekly = computed(() => Math.max(1, ...history.weeklyMinutes.map(day => day.minutes)))
</script>

<template>
  <aside
    class="fixed right-0 top-0 z-[97] flex h-full w-full max-w-md flex-col overflow-y-auto rounded-l-3xl border-l border-slate-200 bg-white shadow-2xl"
  >
    <header class="flex items-center gap-3 px-6 pb-2 pt-6">
      <span class="flex h-10 w-10 items-center justify-center rounded-2xl bg-brand/25 text-brand-strong">
        <IconTrees :size="22" />
      </span>
      <div class="flex-1">
        <h2 class="text-lg font-bold text-slate-800">{{ $t('garden.title') }}</h2>
        <p class="text-xs text-slate-500">{{ $t('garden.subtitle') }}</p>
      </div>
      <button
        class="flex h-9 w-9 items-center justify-center rounded-full text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
        :aria-label="$t('settings.buttons.close')"
        @click="openPanels.garden = false"
      >
        <IconX :size="20" />
      </button>
    </header>

    <!-- 资源条：阳光 + 连续天数（累计专注在「记录」里） -->
    <div class="mx-6 mt-3 grid grid-cols-2 gap-3">
      <div class="rounded-2xl bg-slate-50 px-3 py-3 text-center">
        <IconSun :size="18" class="mx-auto mb-1 text-amber-500" />
        <p class="text-lg font-bold leading-none text-slate-800" data-testid="sunlight-value">{{ garden.sunlight }}</p>
        <p class="mt-1 text-[11px] text-slate-500">{{ $t('garden.sunlight') }}</p>
      </div>
      <div class="rounded-2xl bg-slate-50 px-3 py-3 text-center">
        <IconFlame :size="18" class="mx-auto mb-1 text-brand-strong" />
        <p class="text-lg font-bold leading-none text-slate-800">{{ garden.streak }}</p>
        <p class="mt-1 text-[11px] text-slate-500">{{ $t('garden.streak') }}</p>
      </div>
    </div>

    <div class="mx-6 mt-3 flex gap-1 rounded-2xl bg-slate-100 p-1">
      <button
        class="flex flex-1 items-center justify-center gap-1.5 rounded-xl px-2 py-2 text-xs font-bold transition"
        :class="tab === 'forest' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-700'"
        data-testid="tab-forest"
        @click="tab = 'forest'"
      >
        <IconTrees :size="16" />{{ $t('garden.tabs.forest') }}
      </button>
      <button
        class="flex flex-1 items-center justify-center gap-1.5 rounded-xl px-2 py-2 text-xs font-bold transition"
        :class="tab === 'garden' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-700'"
        data-testid="tab-gardening"
        @click="tab = 'garden'"
      >
        <IconLeaf :size="16" />{{ $t('garden.tabs.gardening') }}
      </button>
      <button
        class="flex flex-1 items-center justify-center gap-1.5 rounded-xl px-2 py-2 text-xs font-bold transition"
        :class="tab === 'records' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-700'"
        data-testid="tab-records"
        @click="tab = 'records'"
      >
        <IconList :size="16" />{{ $t('garden.tabs.records') }}
      </button>
    </div>

    <!-- 首次引导 -->
    <section
      v-if="!guideClosed && tab !== 'records'"
      class="mx-6 mt-3 rounded-2xl border border-brand/40 bg-brand/10 px-4 py-3"
    >
      <div class="flex items-start justify-between gap-2">
        <p class="text-xs leading-relaxed text-slate-700">
          <strong>{{ $t('garden.guide.title') }}</strong><br>
          {{ $t('garden.guide.step1') }}<br>
          {{ $t('garden.guide.step2') }}<br>
          {{ $t('garden.guide.step3') }}
        </p>
        <button
          class="shrink-0 rounded-full px-2 py-1 text-[11px] font-bold text-slate-500 transition hover:bg-white"
          @click="closeGuide"
        >
          {{ $t('garden.guide.close') }}
        </button>
      </div>
    </section>

    <!-- 状态行：阳光不足时的差额 -->
    <p
      v-if="hint"
      class="mx-6 mt-3 rounded-2xl bg-amber-50 px-4 py-2 text-xs font-bold text-amber-700"
      data-testid="sunlight-hint"
    >
      {{ hint }}
    </p>

    <template v-if="tab === 'forest'">
      <section class="mx-6 mb-3 mt-3 rounded-3xl border border-slate-200 bg-[#f7fafc] p-4">
        <div v-if="garden.treeCount === 0" class="flex flex-col items-center gap-2 py-8 text-center">
          <IconTrees :size="40" class="text-slate-300" />
          <p class="text-sm font-bold text-slate-600">{{ $t('garden.empty') }}</p>
          <p class="max-w-[16rem] text-xs leading-relaxed text-slate-400">{{ $t('garden.emptyHint') }}</p>
        </div>

        <div v-else class="flex flex-wrap items-end justify-center gap-1">
          <button
            v-for="tree in shown"
            :key="tree.id"
            data-testid="tree-cell"
            :data-tree-id="tree.id"
            :data-stage="garden.stageOf(tree)"
            :data-species="tree.species"
            :class="['flex flex-col items-center gap-1 rounded-2xl p-1 transition', selectedId === tree.id ? 'bg-white shadow-sm' : 'hover:bg-white']"
            @click="select(tree.id)"
          >
            <PlantSvg
              :species="tree.species"
              :stage="garden.stageOf(tree)"
              :dead="tree.withered"
              :size="38 + garden.stageOf(tree) * 9"
            />
            <span
              class="text-[10px] leading-none tracking-tighter text-slate-400"
              data-testid="stage-dots"
              :data-filled="garden.stageOf(tree)"
              :data-total="MAX_STAGE + 1"
            >{{ '●'.repeat(garden.stageOf(tree) + 1) }}{{ '○'.repeat(MAX_STAGE - garden.stageOf(tree)) }}</span>
            <span v-if="tree.withered" class="text-[10px] font-bold text-amber-600">{{ $t('garden.withered') }}</span>
          </button>
        </div>

        <p v-if="garden.treeCount > 0" class="mt-3 text-center text-[11px] text-slate-400">
          {{ $t('garden.treeCount', { n: garden.treeCount }) }}
        </p>
      </section>

      <!-- 选中栏：点一棵树后可浇水 / 再种一株 -->
      <section
        v-if="selected"
        class="sticky bottom-0 mx-4 mb-4 flex items-center gap-2 rounded-3xl border border-slate-200 bg-white px-4 py-3 shadow-lg"
      >
        <div class="min-w-0 flex-1">
          <p class="truncate text-sm font-bold text-slate-800">
            {{ speciesName(selected.species) }}
            <span class="text-xs font-normal text-slate-500">
              {{ $t('garden.stage', { a: garden.stageOf(selected), b: MAX_STAGE }) }}
            </span>
          </p>
          <p class="text-[11px] text-slate-500">
            <template v-if="selected.withered">{{ $t('garden.witheredHint') }}</template>
            <template v-else-if="!garden.canWater(selected)">{{ $t('garden.waterLimit', { n: WATER_LIMIT }) }}</template>
            <template v-else>{{ $t('garden.waterHint') }}</template>
          </p>
        </div>
        <button
          data-testid="tree-water"
          :data-tree-id="selected.id"
          :disabled="!canWater"
          class="flex shrink-0 items-center gap-1.5 rounded-full bg-brand-strong px-3 py-2 text-xs font-bold text-white transition enabled:hover:brightness-110 disabled:bg-slate-200 disabled:text-slate-400"
          @click="waterSelected"
        >
          <IconDroplet :size="15" />{{ $t('garden.waterCost', { n: waterCost }) }}
        </button>
      </section>
      <p
        v-else-if="garden.treeCount > 0"
        class="mx-6 mb-4 text-center text-[11px] text-slate-400"
      >
        {{ $t('garden.selectTree') }}
      </p>
    </template>

    <template v-else-if="tab === 'garden'">
      <section class="mx-6 mb-3 mt-3 rounded-3xl border border-slate-200 bg-[#f7fafc] p-4">
        <p class="text-xs font-bold text-slate-700">{{ $t('garden.priceRule') }}</p>
        <p class="mt-1 text-[11px] leading-relaxed text-slate-500">{{ $t('garden.witherRule') }}</p>
      </section>

      <!-- 手动种树 -->
      <section class="mx-6 mb-4">
        <h3 class="mb-2 flex items-center gap-1.5 text-xs font-bold text-slate-500">
          <IconPlant2 :size="15" />{{ $t('garden.plantTitle') }}
        </h3>
        <div class="flex flex-wrap gap-1.5">
          <button
            v-for="id in garden.unlocked"
            :key="id"
            data-testid="species-chip"
            :data-species="id"
            :data-unlocked="true"
            :class="['flex items-center gap-1.5 rounded-full px-2.5 py-1.5 text-[11px] font-bold transition', pickedSpecies === id ? 'bg-brand-strong text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200']"
            @click="pickedSpecies = id"
          >
            <PlantSvg :species="id" :stage="2" :size="16" />
            {{ speciesName(id) }}
          </button>
        </div>
        <button
          data-testid="plant-manual"
          :disabled="!canPlant"
          class="mt-3 flex w-full items-center justify-center gap-2 rounded-2xl bg-brand-strong px-4 py-3 text-sm font-bold text-white transition enabled:hover:brightness-110 disabled:bg-slate-200 disabled:text-slate-400"
          @click="plantPicked"
        >
          <IconPlant2 :size="18" />{{ $t('garden.plantCost', { n: PLANT_COST }) }}
        </button>
        <p v-if="garden.treeCount >= garden.plotCapacity" class="mt-2 text-[11px] font-bold text-amber-600">
          {{ $t('garden.plotFull') }}
        </p>
      </section>

      <!-- 阳光商店 -->
      <section class="mx-6 mb-4">
        <h3 class="mb-2 flex items-center gap-1.5 text-xs font-bold text-slate-500">
          <IconSun :size="15" />{{ $t('garden.shop') }}
        </h3>
        <p class="mb-2 text-[11px] leading-relaxed text-slate-500">{{ $t('garden.shopHint') }}</p>
        <div class="grid grid-cols-2 gap-2">
          <div
            v-for="id in locked"
            :key="id"
            class="flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-3 py-2"
          >
            <PlantSvg :species="id" :stage="3" :size="30" />
            <div class="min-w-0 flex-1">
              <p class="truncate text-xs font-bold text-slate-700">{{ speciesName(id) }}</p>
              <p class="text-[11px] text-amber-600">☀️ {{ PLANT_SPECIES[id].cost }}</p>
            </div>
            <button
              data-testid="shop-unlock"
              :data-species="id"
              :disabled="garden.sunlight < PLANT_SPECIES[id].cost"
              class="shrink-0 rounded-full bg-brand-strong px-2.5 py-1 text-[11px] font-bold text-white transition enabled:hover:brightness-110 disabled:bg-slate-200 disabled:text-slate-400"
              @click="unlock(id)"
            >
              {{ garden.sunlight < PLANT_SPECIES[id].cost ? $t('garden.keepFocusing') : $t('garden.unlock') }}
            </button>
          </div>
        </div>
      </section>

      <!-- 扩建花园 -->
      <section class="mx-6 mb-4">
        <h3 class="mb-2 flex items-center gap-1.5 text-xs font-bold text-slate-500">
          <IconChevronRight :size="15" />{{ $t('garden.expand') }}
        </h3>
        <p class="mb-2 text-[11px] leading-relaxed text-slate-500">{{ $t('garden.expandHint') }}</p>
        <div class="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-3">
          <p class="flex-1 text-xs font-bold text-slate-700">
            {{ $t('garden.plot', { a: garden.treeCount, b: garden.plotCapacity }) }}
          </p>
          <button
            data-testid="expand-garden"
            :disabled="!canExpand"
            class="flex items-center gap-1.5 rounded-full bg-brand-strong px-3 py-2 text-xs font-bold text-white transition enabled:hover:brightness-110 disabled:bg-slate-200 disabled:text-slate-400"
            @click="expand"
          >
            <IconChevronRight :size="15" />
            {{ garden.nextExpandCost === null ? $t('garden.expandMax') : $t('garden.expandCost', { n: garden.nextExpandCost }) }}
          </button>
        </div>
      </section>
    </template>

    <template v-else>
      <section class="mx-6 mb-4 mt-3 rounded-3xl border border-slate-200 bg-[#f7fafc] p-4">
        <p class="mb-3 text-xs font-bold text-slate-500">{{ $t('garden.weekly') }}</p>
        <div class="flex h-24 items-end justify-between gap-1.5">
          <div v-for="day in history.weeklyMinutes" :key="day.day" class="flex flex-1 flex-col items-center gap-1">
            <span class="text-[10px] font-bold text-slate-500">{{ day.minutes || '' }}</span>
            <div
              class="w-full rounded-t-lg bg-brand-strong/70 transition-all"
              :style="{ height: Math.max(4, Math.round((day.minutes / maxWeekly) * 68)) + 'px' }"
            />
            <span class="text-[10px] text-slate-400">{{ day.label }}</span>
          </div>
        </div>
      </section>

      <section class="mx-6 mb-4">
        <h3 class="mb-2 flex items-center gap-1.5 text-xs font-bold text-slate-500">
          <IconLogin :size="15" />{{ $t('garden.logins') }}
        </h3>
        <ul v-if="history.recentLogins.length > 0" class="flex flex-col gap-1.5">
          <li
            v-for="login in history.recentLogins.slice(0, 8)"
            :key="login.id"
            class="flex items-center justify-between rounded-2xl bg-slate-50 px-4 py-2.5 text-xs text-slate-600"
          >
            <span class="font-bold text-slate-700">{{ formatDay(login.at) }}</span>
            <span>{{ formatTime(login.at) }}</span>
          </li>
        </ul>
        <p v-else class="rounded-2xl bg-slate-50 px-4 py-4 text-center text-xs text-slate-400">
          {{ $t('garden.noLogins') }}
        </p>
      </section>

      <section class="mx-6 mb-4">
        <h3 class="mb-2 flex items-center gap-1.5 text-xs font-bold text-slate-500">
          <IconCheck :size="15" />{{ $t('garden.focusRecords') }}
        </h3>
        <ul v-if="history.recentRecords.length > 0" class="flex flex-col gap-1.5">
          <li
            v-for="record in history.recentRecords.slice(0, 12)"
            :key="record.id"
            class="flex items-center justify-between rounded-2xl bg-slate-50 px-4 py-2.5 text-xs text-slate-600"
          >
            <span class="font-bold text-slate-700">{{ formatDay(record.startedAt) }} {{ formatTime(record.startedAt) }}</span>
            <span class="flex items-center gap-1.5">
              <span>{{ record.minutes }} min</span>
              <span
                class="rounded-full px-2 py-0.5 text-[10px] font-bold"
                :class="record.completed ? 'bg-emerald-50 text-emerald-600' : 'bg-slate-200 text-slate-500'"
              >{{ record.completed ? $t('garden.completed') : $t('garden.abandoned') }}</span>
            </span>
          </li>
        </ul>
        <p v-else class="rounded-2xl bg-slate-50 px-4 py-4 text-center text-xs text-slate-400">
          {{ $t('garden.noRecords') }}
        </p>
      </section>
    </template>

    <footer class="mt-auto flex items-center justify-between gap-3 px-6 py-5">
      <p class="text-[11px] leading-relaxed text-slate-400">{{ $t('garden.hint') }}</p>
      <button
        class="flex items-center gap-1.5 rounded-full px-3 py-2 text-xs transition"
        :class="confirmClear ? 'bg-red-50 text-red-600' : 'text-slate-400 hover:bg-slate-100 hover:text-slate-600'"
        @click="clear"
      >
        <IconTrash :size="16" />
        {{ confirmClear ? $t('garden.clearConfirm') : $t('garden.clear') }}
      </button>
    </footer>
  </aside>
</template>
