<script setup lang="ts">
import { IconAlertTriangle } from '@tabler/icons-vue'
import { useOpenPanels } from '~~/stores/openpanels'

const openPanels = useOpenPanels()

/** 贴着触发按钮定位（按钮在右上角，小窗出现在它下方偏左） */
const style = computed(() => {
  const rect = openPanels.pendingRect
  if (!rect) {
    return { top: '72px', right: '16px' }
  }

  return {
    top: Math.round(rect.bottom + 10) + 'px',
    left: Math.round(Math.max(12, rect.left - 220)) + 'px'
  }
})
</script>

<template>
  <Teleport to="body">
    <div
      v-if="openPanels.pending"
      class="fixed z-[70] w-56 rounded-2xl border border-slate-200 bg-white p-3 shadow-xl"
      :style="style"
      @click.stop
    >
      <p class="flex items-start gap-2 text-xs leading-relaxed text-slate-600">
        <IconAlertTriangle :size="16" class="mt-0.5 shrink-0 text-amber-500" />
        <span>{{ $t('focus.distract.body') }}</span>
      </p>

      <div class="mt-2 flex items-center justify-end gap-1">
        <button
          class="rounded-full px-2.5 py-1.5 text-[11px] font-bold text-slate-400 transition hover:bg-slate-100 hover:text-slate-600"
          @click="openPanels.cancel()"
        >
          {{ $t('focus.distract.stayShort') }}
        </button>
        <button
          class="rounded-full bg-brand-strong px-2.5 py-1.5 text-[11px] font-bold text-white transition hover:brightness-110"
          @click="openPanels.confirm()"
        >
          {{ $t('focus.distract.openAnyway') }}
        </button>
      </div>
    </div>
  </Teleport>
</template>
