<script setup lang="ts">
import { IconAlertTriangle } from '@tabler/icons-vue'
import { useOpenPanels } from '~~/stores/openpanels'

const openPanels = useOpenPanels()
const { confirmAccess } = usePanelAccess()

/** 贴着触发按钮定位（按钮在右上角，小窗出现在它下方偏左） */
const style = computed(() => {
  const rect = openPanels.pendingRect
  if (!rect) {
    return {
      top: '72px',
      right: '16px',
      '--tip-origin-x': '200px',
      '--tip-origin-y': '0px'
    }
  }

  const panelTop = rect.bottom + 10
  const panelLeft = Math.max(12, rect.left - 220)
  return {
    top: Math.round(panelTop) + 'px',
    left: Math.round(panelLeft) + 'px',
    '--tip-origin-x': Math.round(rect.left + rect.width / 2 - panelLeft) + 'px',
    '--tip-origin-y': Math.round(rect.top + rect.height / 2 - panelTop) + 'px'
  }
})

const onKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && openPanels.pending) {
    openPanels.cancel()
  }
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-from-class="opacity-0"
      enter-active-class="transition duration-150"
      leave-to-class="opacity-0"
      leave-active-class="transition duration-150"
    >
      <button
        v-if="openPanels.pending"
        type="button"
        class="fixed inset-0 z-[69] cursor-default bg-slate-900/10"
        :aria-label="$t('settings.buttons.close')"
        @click="openPanels.cancel()"
      />
    </Transition>
    <Transition
      enter-from-class="tip-enter-from"
      enter-active-class="tip-enter-active"
      leave-to-class="tip-leave-to"
      leave-active-class="tip-leave-active"
    >
      <div
        v-if="openPanels.pending"
        class="fixed z-[70] w-56 rounded-2xl border border-slate-200 bg-white p-3 shadow-xl tip-surface"
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
            @click="confirmAccess()"
          >
            {{ $t('focus.distract.openAnyway') }}
          </button>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.tip-surface {
  clip-path: circle(150vmax at var(--tip-origin-x, 200px) var(--tip-origin-y, 0px));
}

.tip-enter-from,
.tip-leave-to {
  opacity: 0;
  clip-path: circle(0px at var(--tip-origin-x, 200px) var(--tip-origin-y, 0px));
}

.tip-enter-active,
.tip-leave-active {
  transition:
    clip-path 260ms cubic-bezier(0.22, 1, 0.36, 1),
    opacity 150ms ease;
}
</style>
