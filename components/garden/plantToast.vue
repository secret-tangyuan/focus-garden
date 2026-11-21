<script setup lang="ts">
import { IconTrees } from '@tabler/icons-vue'
import { useGarden } from '~~/stores/garden'

const garden = useGarden()
const visible = ref(false)
const shownAt = ref(0)

watch(() => garden.lastPlantedAt, (value) => {
  if (!value || value === shownAt.value) { return }
  shownAt.value = value
  visible.value = true
  setTimeout(() => { visible.value = false }, 3200)
})
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-from-class="-translate-y-6 opacity-0"
      enter-active-class="transition duration-300 ease-out"
      leave-to-class="-translate-y-6 opacity-0"
      leave-active-class="transition duration-300 ease-in"
    >
      <div
        v-if="visible"
        class="fixed left-1/2 top-6 z-[90] flex -translate-x-1/2 items-center gap-3 rounded-2xl border border-brand/40 bg-white px-5 py-3 text-sm shadow-xl"
      >
        <span class="flex h-9 w-9 items-center justify-center rounded-full bg-brand/25 text-brand-strong">
          <IconTrees :size="20" />
        </span>
        <span class="font-bold text-slate-800">{{ $t('garden.planted') }}</span>
        <span class="text-xs text-slate-500">{{ $t('garden.total') }} {{ garden.totalMinutes }} min</span>
      </div>
    </Transition>
  </Teleport>
</template>
