<script setup lang="ts">
import { IconBrandGithub } from '@tabler/icons-vue'
import { ButtonImportance } from '../base/types/button'
import Button from '~~/components/base/uiButton.vue'
import { useMain } from '~~/stores/main'

const mainStore = useMain()
</script>

<template>
  <div class="flex flex-col gap-6">
    <!-- 双作者：本站在左，原作者在右 -->
    <div class="grid grid-cols-2 gap-3">
      <!-- 左：秘密小汤圆 -->
      <div class="flex flex-col items-center gap-2 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-center">
        <img src="/tangyuan.svg" width="56" height="56" class="inline-block" alt="秘密小汤圆">
        <div class="text-base font-bold text-slate-800">秘密小汤圆</div>
        <div class="text-xs text-slate-500">{{ $t('settings.about.project') }}</div>
        <sup class="text-[10px] text-slate-400" v-text="mainStore.version" />
      </div>

      <!-- 右：原作者 -->
      <div class="flex flex-col items-center gap-2 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-center">
        <img src="/favicon.svg" width="56" height="56" class="inline-block" alt="FocusTide">
        <div class="text-base font-bold text-slate-800">FocusTide</div>
        <div class="text-xs text-slate-500">{{ $t('settings.about.original') }}</div>
        <Button
          :importance="ButtonImportance.Filled"
          link
          dark
          no-default-style
          no-content-theme
          href="https://github.com/Hanziness/FocusTide"
          inner-class="flex flex-row items-center gap-1 text-xs text-slate-600"
          bg-class="bg-transparent"
        >
          <IconBrandGithub :size="16" />
          <span v-text="$t('settings.about.source')" />
        </Button>
      </div>
    </div>

    <p class="text-xs leading-relaxed text-slate-500" v-text="$t('settings.about.licenseNote')" />

    <div class="flex flex-col items-center gap-2 border-t border-slate-200 pt-4 text-center">
      <p class="text-xs text-slate-500" v-text="$t('settings.about.supportBody')" />
    </div>
  </div>
</template>
