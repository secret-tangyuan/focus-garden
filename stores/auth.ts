import { defineStore } from 'pinia'

export interface SessionUser {
  username: string
  display_name: string
  email?: string
  avatar?: string
  role?: string
  must_change_pw?: boolean
}

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
    checked: false
  }),

  getters: {
    /** 顶栏显示的名字 */
    displayName: state => state.user?.display_name || state.user?.username || ''
  },

  actions: {
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
      try {
        const response = await fetch('/auth/session', {
          headers: { Accept: 'application/json' },
          credentials: 'include'
        })
        if (!response.ok) { return }
        const data = await response.json()
        this.authenticated = !!data.authenticated
        this.user = data.authenticated ? data.user : null
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
      try {
        const body = new URLSearchParams()
        body.set('username', username.trim())
        body.set('password', password)
        body.set('mode', 'sso')
        body.set('next', location.origin + location.pathname)

        const response = await fetch('/auth/login', {
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
      try {
        await fetch('/auth/logout', {
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
