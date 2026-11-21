import { defineStore } from 'pinia'
import { useSettings } from '~~/stores/settings'

/**
 * 专注模式（强制全屏）
 * - 开启后开始计时会请求全屏
 * - 计时途中退出全屏会被遮罩拦住，可选择自动暂停计时
 */
export const useFocusMode = defineStore('focusMode', {
  state: () => ({
    /** 用户是否已经进入过专注模式（进入过就不再每次弹出门页） */
    entered: false,
    /** 当前是否处于全屏 */
    isFullscreen: false,
    /** 是否需要阻止操作（退出了全屏） */
    blocked: false,
    /** 本次专注中退出全屏的次数 */
    exitCount: 0,
    /** 是否因为退出全屏而暂停了计时（回到全屏后自动继续） */
    pausedByExit: false
  }),

  getters: {
    /** 是否启用强制全屏（在设置里可关） */
    enabled: () => useSettings().focus.fullscreen,
    /** 退出全屏时是否自动暂停计时 */
    autoPause: () => useSettings().focus.pauseOnExit,
    /** 是否应当显示「回到全屏」的拦截层 */
    needsFullscreen: state => useSettings().focus.fullscreen && state.blocked
  },

  actions: {
    /** 请求进入全屏（必须在用户手势中调用） */
    async requestFullscreen () {
      if (!import.meta.client) { return false }
      if (document.fullscreenElement) {
        this.isFullscreen = true
        return true
      }

      const element = document.documentElement as HTMLElement & {
        webkitRequestFullscreen?: () => Promise<void>
      }

      try {
        const request = element.requestFullscreen
          ? element.requestFullscreen()
          : element.webkitRequestFullscreen
            ? element.webkitRequestFullscreen()
            : null

        if (!request) { return false }

        // 某些浏览器/环境下 promise 不会 settle，加超时兜底，不阻塞计时
        await Promise.race([
          request,
          new Promise(resolve => setTimeout(resolve, 1500))
        ])
        this.isFullscreen = true
        this.blocked = false
        this.entered = true
        return true
      } catch (err) {
        console.warn('Fullscreen request was rejected', err)
        return false
      }
    },

    /**
     * 退出全屏（用户主动「暂停并退出」时使用）。
     * 注意：不清掉 entered —— 退出全屏不等于回到入口页，
     * 否则「暂停并退出」会把入口页重新盖上来。
     */
    async exitFullscreen () {
      if (!import.meta.client) { return }
      if (document.fullscreenElement) {
        try {
          const exit = (document as Document & { webkitExitFullscreen?: () => Promise<void> }).webkitExitFullscreen
          if (exit) {
            await exit.call(document)
          } else {
            await document.exitFullscreen()
          }
        } catch (err) {
          console.warn('Fullscreen exit was rejected', err)
        }
      }
      this.isFullscreen = false
      this.blocked = false
    },

    /** 同步 fullscreenchange 事件的状态 */
    syncFullscreenState () {
      if (!import.meta.client) { return }
      this.isFullscreen = !!document.fullscreenElement
    },

    /** 计时中退出了全屏 */
    markExitDuringSession () {
      this.blocked = true
      this.exitCount += 1
    },

    /** 标记计时是被「退出全屏」暂停的 */
    markPausedByExit () {
      this.pausedByExit = true
    },

    /** 清掉「因退出全屏而暂停」的标记 */
    clearPausedByExit () {
      this.pausedByExit = false
    }
  }
})
