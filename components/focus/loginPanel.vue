<script setup lang="ts">
import { IconLogin, IconX, IconAlertCircle, IconCircleCheck } from '@tabler/icons-vue'
import { useAuth } from '~~/stores/auth'
import { useRuntimeConfig } from '#imports'

const auth = useAuth()
const runtimeConfig = useRuntimeConfig()

const username = ref('')
const password = ref('')
const usernameRef = ref<HTMLInputElement | null>(null)

watch(() => auth.loginOpen, (open) => {
  if (open) {
    auth.error = ''
    nextTick(() => usernameRef.value?.focus())
  }
})

/** 贴在触发按钮下方（跟提醒小窗一个位置逻辑） */
const style = computed(() => {
  const rect = auth.loginRect
  if (!rect) {
    return { top: '72px', right: '16px' }
  }
  return {
    top: Math.round(rect.bottom + 10) + 'px',
    left: Math.round(Math.max(12, rect.left - 244)) + 'px'
  }
})

const submit = async () => {
  const ok = await auth.login(username.value, password.value)
  if (ok) {
    password.value = ''
  }
}

/** 完整登录页（注册 / 忘记密码在这里） */
const fullLoginUrl = computed(() => {
  const base = String(runtimeConfig.public.IDENTITY_BASE_URL || '').replace(/\/$/, '')
  const back = encodeURIComponent(location.origin + location.pathname)
  return base ? base + '/login?next=' + back : ''
})

const openFullLogin = () => {
  if (!fullLoginUrl.value) { return }
  window.open(fullLoginUrl.value, '_blank')
}
</script>

<template>
  <Teleport to="body">
    <!-- 精简版登录：贴在按钮旁的小窗，不遮挡整页 -->
    <div
      v-if="auth.loginOpen"
      class="fixed z-[96] w-60 rounded-2xl border border-slate-200 bg-white p-4 shadow-xl"
      :style="style"
      @click.stop
    >
      <div class="mb-3 flex items-center gap-2">
        <span class="flex h-8 w-8 items-center justify-center rounded-xl bg-brand/25 text-brand-strong">
          <IconLogin :size="16" />
        </span>
        <div class="flex-1">
          <h2 class="text-sm font-bold text-slate-800">{{ $t('login.title') }}</h2>
          <p class="text-[11px] text-slate-500">{{ $t('login.subtitle') }}</p>
        </div>
        <button
          class="flex h-7 w-7 items-center justify-center rounded-full text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
          :aria-label="$t('settings.buttons.close')"
          @click="auth.closeLogin()"
        >
          <IconX :size="16" />
        </button>
      </div>

      <form class="flex flex-col gap-2" @submit.prevent="submit">
        <input
          ref="usernameRef"
          v-model="username"
          type="text"
          autocomplete="username"
          :placeholder="$t('login.usernamePlaceholder')"
          :aria-label="$t('login.username')"
          class="rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none transition focus:border-brand-strong focus:ring-2 focus:ring-brand/40"
        >
        <input
          v-model="password"
          type="password"
          autocomplete="current-password"
          :placeholder="$t('login.passwordPlaceholder')"
          :aria-label="$t('login.password')"
          class="rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none transition focus:border-brand-strong focus:ring-2 focus:ring-brand/40"
        >

        <p
          v-if="auth.error"
          class="flex items-start gap-1.5 rounded-xl bg-red-50 px-2.5 py-1.5 text-[11px] leading-relaxed text-red-600"
        >
          <IconAlertCircle :size="13" class="mt-0.5 shrink-0" />
          <span>{{ auth.error }}</span>
        </p>

        <button
          type="submit"
          :disabled="auth.busy"
          class="rounded-full bg-brand-strong px-4 py-2 text-xs font-bold text-white transition hover:brightness-110 disabled:opacity-60"
        >
          {{ auth.busy ? $t('login.submitting') : $t('login.submit') }}
        </button>
      </form>

      <button
        class="mt-2 w-full text-center text-[11px] text-slate-400 underline-offset-4 transition hover:text-slate-600 hover:underline"
        @click="openFullLogin"
      >
        {{ $t('login.full') }}
      </button>
    </div>

    <!-- 已登录提示 -->
    <Transition
      enter-from-class="-translate-y-6 opacity-0"
      enter-active-class="transition duration-300 ease-out"
      leave-to-class="-translate-y-6 opacity-0"
      leave-active-class="transition duration-300 ease-in"
    >
      <div
        v-if="auth.authenticated && !auth.loginOpen"
        class="fixed left-1/2 top-6 z-[90] flex -translate-x-1/2 items-center gap-2 rounded-2xl border border-emerald-200 bg-white px-4 py-2.5 text-sm shadow-xl"
      >
        <IconCircleCheck :size="18" class="text-emerald-500" />
        <span class="font-bold text-slate-800">{{ $t('login.welcome') }}</span>
        <span class="text-xs text-slate-500">{{ auth.displayName }}</span>
      </div>
    </Transition>
  </Teleport>
</template>
