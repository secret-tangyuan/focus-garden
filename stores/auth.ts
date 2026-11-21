import { defineStore } from 'pinia'
import { useRuntimeConfig } from '#imports'

export interface SessionUser {
  username: string
  display_name: string
  email?: string
  avatar?: string
  role?: string
  must_change_pw?: boolean
}

/** 续签提前量：剩余有效期少于这个值时就续（毫秒） */
const RENEW_LEAD = 30 * 60 * 1000

/** 两次续签之间的最小间隔（毫秒），避免频繁切页面就续 */
const RENEW_MIN_GAP = 5 * 60 * 1000

/** 续签定时器 */
let renewTimer: ReturnType<typeof setTimeout> | null = null

/** 上次续签的时间 */
let lastRenewAt = 0

export const useAuth = defineStore('auth', {
  state: () => ({
    /** 精简版登录面板是否打开 */
    loginOpen: false,
    /** 登录小窗贴着哪个按钮显示 */
    loginRect: null as { top: number, right: number, bottom: number, left: number } | null,
    /** 是否已登录 */
    authenticated: false,
    /** 当前用户 */
    user: null as SessionUser | null,
    /** 登录中的错误提示（页面内展示，不用原生弹窗） */
    error: '',
    /** 请求中 */
    busy: false,
    /** 已检查过会话 */
    checked: false,
    /** 会话是否已过期（续签失败） */
    expired: false
  }),

  getters: {
    /** 顶栏显示的名字 */
    displayName: state => state.user?.display_name || state.user?.username || '',

    /** 是否配置了身份服务（没配置就不显示登录入口） */
    identityReady: () => {
      const config = useRuntimeConfig().public
      return !!(config.IDENTITY_API_LOGIN && config.IDENTITY_API_SESSION)
    }
  },

  actions: {
    /**
     * 排程续签：会话快过期时（剩余有效期不足 30 分钟）自动续一次，免密。
     * 排程依据服务端给的 expires_at，而不是固定间隔。
     */
    scheduleRenew (scope: string, expiresAt?: number) {
      if (renewTimer) {
        clearTimeout(renewTimer)
        renewTimer = null
      }
      if (scope !== 'tmp') { return }

      const endpoint = String(useRuntimeConfig().public.IDENTITY_API_RENEW || '')
      if (!endpoint) { return }

      const remaining = expiresAt ? expiresAt * 1000 - Date.now() : 0
      if (remaining <= 0) {
        renewTimer = setTimeout(() => { void this.renew() }, 60 * 1000)
        return
      }

      // 提前量最多 30 分钟，且不超过剩余时间的一半
      const lead = Math.min(RENEW_LEAD, remaining / 2)
      const delay = Math.max(60 * 1000, remaining - lead)

      renewTimer = setTimeout(() => { void this.renew() }, delay)
    },

    /** 从后台切回前台：会话快过期时立刻续一次 */
    async renewIfStale () {
      if (!this.authenticated) { return }
      if (Date.now() - lastRenewAt < RENEW_MIN_GAP) { return }
      await this.renew()
    },

    /** 续签一次短效会话 */
    async renew () {
      const endpoint = String(useRuntimeConfig().public.IDENTITY_API_RENEW || '')
      if (!endpoint) { return false }

      try {
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: { Accept: 'application/json' },
          credentials: 'include'
        })

        if (response.status === 401) {
          this.authenticated = false
          this.user = null
          this.expired = true
          return false
        }

        const data = await response.json().catch(() => ({}))
        if (!response.ok || !data.ok) { return false }

        this.expired = false
        lastRenewAt = Date.now()
        this.scheduleRenew(String(data.scope || 'tmp'), Number(data.expires_at || 0) || undefined)
        return true
      } catch (err) {
        console.warn('renew failed', err)
        return false
      }
    },

    openLogin (rect?: { top: number, right: number, bottom: number, left: number } | null) {
      this.error = ''
      this.loginRect = rect ?? null
      this.loginOpen = true
    },

    closeLogin () {
      this.loginOpen = false
      this.loginRect = null
      this.error = ''
    },

    /** 读取当前会话（页面加载时调一次） */
    async fetchSession () {
      const endpoint = String(useRuntimeConfig().public.IDENTITY_API_SESSION || '')
      if (!endpoint) { this.checked = true; return }

      try {
        const response = await fetch(endpoint, {
          headers: { Accept: 'application/json' },
          credentials: 'include'
        })
        if (!response.ok) { return }
        const data = await response.json()
        this.authenticated = !!data.authenticated
        this.user = data.authenticated ? data.user : null
        this.expired = false
        if (this.authenticated) {
          lastRenewAt = Date.now()
          this.scheduleRenew(String(data.scope || ''), Number(data.expires_at || 0) || undefined)
        }
      } catch (err) {
        console.warn('session check failed', err)
      } finally {
        this.checked = true
      }
    },

    /** 登录：精简版只留账号 + 密码 */
    async login (username: string, password: string) {
      this.error = ''

      if (!username.trim() || !password) {
        this.error = '请输入用户名和密码'
        return false
      }

      this.busy = true
      const config = useRuntimeConfig().public
      const endpoint = String(config.IDENTITY_API_LOGIN || '')
      if (!endpoint) {
        this.error = '未配置身份服务'
        this.busy = false
        return false
      }

      try {
        const body = new URLSearchParams()
        body.set('username', username.trim())
        body.set('password', password)
        body.set('next', location.origin + location.pathname)

        const response = await fetch(endpoint, {
          method: 'POST',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
          },
          credentials: 'include',
          body
        })

        const data = await response.json().catch(() => ({}))

        if (!response.ok || !data.ok) {
          this.error = data.error || '登录失败，请稍后重试'
          return false
        }

        if (data.must_change_pw) {
          this.error = '该账号需要先修改密码，请在完整登录页处理'
          this.loginOpen = false
          window.open(
            (data.next || location.origin) + '?change=1',
            '_blank'
          )
          return false
        }

        await this.fetchSession()
        this.scheduleRenew('tmp')
        this.loginOpen = false
        return true
      } catch (err) {
        console.warn('login failed', err)
        this.error = '无法连接身份中心，请稍后重试'
        return false
      } finally {
        this.busy = false
      }
    },

    /** 退出登录 */
    async logout () {
      const endpoint = String(useRuntimeConfig().public.IDENTITY_API_LOGOUT || '')
      if (!endpoint) { return }

      try {
        await fetch(endpoint, {
          method: 'POST',
          headers: { Accept: 'application/json' },
          credentials: 'include'
        })
      } catch (err) {
        console.warn('logout failed', err)
      }
      this.authenticated = false
      this.user = null
    }
  }
})
