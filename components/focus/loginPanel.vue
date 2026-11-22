<script setup lang="ts">
import { IconLogin, IconLogout, IconUserCircle, IconX, IconAlertCircle, IconExternalLink } from '@tabler/icons-vue'
import { useI18n } from 'vue-i18n'
import { useAuth } from '~~/stores/auth'
import { useIsland } from '~~/stores/island'
import { useRuntimeConfig } from '#imports'

const auth = useAuth()
const island = useIsland()
const runtimeConfig = useRuntimeConfig()
const { t } = useI18n()

const username = ref('')
const password = ref('')
const usernameRef = ref<HTMLInputElement | null>(null)
const logoutBusy = ref(false)

watch(() => auth.authenticated, (authenticated, previous) => {
  if (authenticated && previous === false) {
    island.show({
      title: String(t('login.welcome')),
      detail: auth.displayName,
      tone: 'success'
    })
    return
  }
  if (!authenticated && previous === true) {
    island.show({
      title: String(t(auth.expired ? 'login.expired' : 'login.loggedOut')),
      tone: auth.expired ? 'warning' : 'info'
    })
  }
})

watch(() => auth.loginOpen, (open) => {
  if (open && !auth.authenticated) {
    auth.error = ''
    nextTick(() => usernameRef.value?.focus())
  }
})

/** 贴在触发按钮下方（跟提醒小窗一个位置逻辑） */
const style = computed(() => {
  const rect = auth.loginRect
  if (!rect) {
    return {
      top: '72px',
      right: '16px',
      '--login-origin-x': '220px',
      '--login-origin-y': '0px'
    }
  }
  const panelTop = rect.bottom + 10
  const panelLeft = Math.max(12, rect.left - 244)
  return {
    top: Math.round(panelTop) + 'px',
    left: Math.round(panelLeft) + 'px',
    '--login-origin-x': Math.round(rect.left + rect.width / 2 - panelLeft) + 'px',
    '--login-origin-y': Math.round(rect.top + rect.height / 2 - panelTop) + 'px'
  }
})

const submit = async () => {
  const ok = await auth.login(username.value, password.value)
  if (ok) {
    password.value = ''
  }
}

const logoutAccount = async () => {
  logoutBusy.value = true
  await auth.logout()
  username.value = ''
  password.value = ''
  auth.closeLogin()
  logoutBusy.value = false
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

const onKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && auth.loginOpen) {
    auth.closeLogin()
  }
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
})
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
        v-if="auth.loginOpen"
        type="button"
        data-testid="login-overlay"
        class="fixed inset-0 z-[97] cursor-default bg-slate-900/10"
        :aria-label="$t('settings.buttons.close')"
        @click="auth.closeLogin()"
      />
    </Transition>

    <!-- 精简版登录：贴在按钮旁的小窗，不遮挡整页 -->
    <Transition
      enter-from-class="login-panel-enter-from"
      enter-active-class="login-panel-enter-active"
      leave-to-class="login-panel-leave-to"
      leave-active-class="login-panel-leave-active"
    >
      <div
        v-if="auth.loginOpen"
        data-testid="login-panel"
        class="fixed z-[98] w-60 rounded-2xl border border-slate-200 bg-white p-4 shadow-xl login-panel-surface"
        :style="style"
        @click.stop
      >
        <div class="mb-3 flex items-center gap-2">
          <span class="flex h-8 w-8 items-center justify-center rounded-xl bg-brand/25 text-brand-strong">
            <IconUserCircle v-if="auth.authenticated" :size="17" />
            <IconLogin v-else :size="16" />
          </span>
          <div class="flex-1">
            <h2 class="text-sm font-bold text-slate-800">
              {{ auth.authenticated ? $t('login.accountTitle') : $t('login.title') }}
            </h2>
            <p class="text-[11px] text-slate-500">
              {{ auth.authenticated ? $t('login.accountBody') : $t('login.subtitle') }}
            </p>
          </div>
          <button
            class="flex h-7 w-7 items-center justify-center rounded-full text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
            :aria-label="$t('settings.buttons.close')"
            @click="auth.closeLogin()"
          >
            <IconX :size="16" />
          </button>
        </div>

        <div v-if="auth.authenticated" class="flex flex-col gap-3">
          <div class="flex items-center gap-3 rounded-2xl bg-slate-50 px-3 py-3">
            <span class="flex h-10 w-10 items-center justify-center rounded-full bg-brand/25 text-brand-strong">
              <IconUserCircle :size="22" />
            </span>
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-bold text-slate-800">{{ auth.displayName }}</p>
              <p class="truncate text-[11px] text-slate-400">@{{ auth.user?.username }}</p>
            </div>
          </div>
          <button
            type="button"
            data-testid="logout-button"
            :disabled="logoutBusy"
            class="flex items-center justify-center gap-1.5 rounded-full bg-red-50 px-4 py-2 text-xs font-bold text-red-600 transition hover:bg-red-100 disabled:opacity-60"
            @click="logoutAccount"
          >
            <IconLogout :size="15" />
            {{ logoutBusy ? $t('login.loggingOut') : $t('login.logout') }}
          </button>
        </div>

        <template v-else>
          <p
            v-if="auth.expired"
            class="mb-2 flex items-start gap-1.5 rounded-xl bg-amber-50 px-2.5 py-1.5 text-[11px] leading-relaxed text-amber-700"
          >
            <IconAlertCircle :size="13" class="mt-0.5 shrink-0" />
            <span>{{ $t('login.expired') }}</span>
          </p>

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

          <p class="mt-2.5 text-center text-[11px] leading-relaxed text-slate-400">
            {{ $t('login.hintBefore') }}
            <button
              class="inline-flex items-center gap-0.5 font-bold text-brand-strong underline-offset-4 transition hover:underline"
              @click="openFullLogin"
            >
              {{ $t('login.hintLink') }}
              <IconExternalLink :size="11" />
            </button>
          </p>
        </template>
      </div>
    </Transition>

  </Teleport>
</template>

<style scoped>
.login-panel-surface {
  clip-path: circle(150vmax at var(--login-origin-x, 220px) var(--login-origin-y, 0px));
}

.login-panel-enter-from,
.login-panel-leave-to {
  opacity: 0;
  clip-path: circle(0px at var(--login-origin-x, 220px) var(--login-origin-y, 0px));
}

.login-panel-enter-active,
.login-panel-leave-active {
  transition:
    clip-path 280ms cubic-bezier(0.22, 1, 0.36, 1),
    opacity 160ms ease;
}

</style>
