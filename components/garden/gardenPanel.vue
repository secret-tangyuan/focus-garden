<script setup lang="ts">
import { IconX, IconTrees, IconClock, IconFlame, IconTrash, IconList, IconLogin, IconCheck } from '@tabler/icons-vue'
import { TreeSpecies, useGarden } from '~~/stores/garden'
import { useHistory } from '~~/stores/history'
import { useOpenPanels } from '~~/stores/openpanels'
import TreeSvg from '~~/components/garden/treeSvg.vue'

const garden = useGarden()
const history = useHistory()
const openPanels = useOpenPanels()

const tab = ref<'forest' | 'records'>('forest')

const speciesList = [
  { id: TreeSpecies.Maple, label: '阔叶' },
  { id: TreeSpecies.Pine, label: '针叶' },
  { id: TreeSpecies.Cherry, label: '樱花' }
]

const confirmClear = ref(false)

const clear = () => {
  if (!confirmClear.value) {
    confirmClear.value = true
    setTimeout(() => { confirmClear.value = false }, 4000)
    return
  }
  garden.clearForest()
  history.clearHistory()
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
  if (date.toDateString() === today) { return '今天' }
  if (date.toDateString() === yesterday) { return '昨天' }
  return `${date.getMonth() + 1}月${date.getDate()}日`
}

const maxWeekly = computed(() => Math.max(1, ...history.weeklyMinutes.map(day => day.minutes)))
</script>

<template>
  <aside
    class="fixed right-0 top-0 z-[96] flex h-full w-full max-w-md flex-col overflow-y-auto rounded-l-3xl border-l border-slate-200 bg-white shadow-2xl"
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

    <div class="mx-6 mt-3 flex gap-1 rounded-2xl bg-slate-100 p-1">
      <button
        class="flex flex-1 items-center justify-center gap-1.5 rounded-xl px-3 py-2 text-xs font-bold transition"
        :class="tab === 'forest' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-700'"
        @click="tab = 'forest'"
      >
        <IconTrees :size="16" />{{ $t('garden.tabs.forest') }}
      </button>
      <button
        class="flex flex-1 items-center justify-center gap-1.5 rounded-xl px-3 py-2 text-xs font-bold transition"
        :class="tab === 'records' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-700'"
        @click="tab = 'records'"
      >
        <IconList :size="16" />{{ $t('garden.tabs.records') }}
      </button>
    </div>

    <div class="grid grid-cols-3 gap-3 px-6 py-4">
      <div class="rounded-2xl bg-slate-50 px-3 py-3 text-center">
        <IconClock :size="18" class="mx-auto mb-1 text-brand-strong" />
        <p class="text-lg font-bold leading-none text-slate-800">{{ garden.totalMinutes }}</p>
        <p class="mt-1 text-[11px] text-slate-500">{{ $t('garden.stats.minutes') }}</p>
      </div>
      <div class="rounded-2xl bg-slate-50 px-3 py-3 text-center">
        <IconTrees :size="18" class="mx-auto mb-1 text-brand-strong" />
        <p class="text-lg font-bold leading-none text-slate-800">{{ garden.treeCount }}</p>
        <p class="mt-1 text-[11px] text-slate-500">{{ $t('garden.stats.trees') }}</p>
      </div>
      <div class="rounded-2xl bg-slate-50 px-3 py-3 text-center">
        <IconFlame :size="18" class="mx-auto mb-1 text-brand-strong" />
        <p class="text-lg font-bold leading-none text-slate-800">{{ garden.streak }}</p>
        <p class="mt-1 text-[11px] text-slate-500">{{ $t('garden.stats.streak') }}</p>
      </div>
    </div>

    <template v-if="tab === 'forest'">
      <section class="mx-6 mb-4 rounded-3xl border border-slate-200 bg-[#f7fafc] p-4">
        <div v-if="garden.treeCount === 0" class="flex flex-col items-center gap-2 py-10 text-center">
          <IconTrees :size="40" class="text-slate-300" />
          <p class="text-sm font-bold text-slate-600">{{ $t('garden.empty') }}</p>
          <p class="max-w-[16rem] text-xs leading-relaxed text-slate-400">{{ $t('garden.emptyHint') }}</p>
        </div>

        <div v-else class="flex flex-wrap items-end justify-center gap-1">
          <div
            v-for="tree in garden.forest.slice(0, 60)"
            :key="tree.id"
            class="flex flex-col items-center"
            :title="tree.minutes + ' min'"
          >
            <TreeSvg :species="tree.species" :stage="garden.stageOf(tree)" :size="34 + garden.stageOf(tree) * 14" />
          </div>
        </div>
      </section>

      <div class="flex flex-wrap items-center gap-3 px-6 text-xs text-slate-500">
        <span v-for="item in speciesList" :key="item.id" class="flex items-center gap-1.5">
          <TreeSvg :species="item.id" :stage="2" :size="20" />
          {{ item.label }} × {{ garden.speciesCount[item.id] ?? 0 }}
        </span>
      </div>
    </template>

    <template v-else>
      <section class="mx-6 mb-4 rounded-3xl border border-slate-200 bg-[#f7fafc] p-4">
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
