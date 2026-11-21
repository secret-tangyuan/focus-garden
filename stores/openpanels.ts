import { defineStore } from 'pinia'

export type PanelName = 'settings' | 'todo' | 'garden'
export type PendingTarget = PanelName | 'login'

export interface TriggerRect {
  top: number
  right: number
  bottom: number
  left: number
}

const useOpenPanels = defineStore('openpanels', {
  state: () => ({
    settings: false,
    todo: false,
    garden: false,
    /** 等待确认打开的面板（非空时在按钮旁显示提醒小窗） */
    pending: null as PendingTarget | null,
    /** 触发按钮的位置（小窗贴着它显示） */
    pendingRect: null as TriggerRect | null
  }),

  actions: {
    /** 请求打开面板：先在按钮旁提示一次 */
    request (name: PendingTarget, rect?: TriggerRect) {
      this.pending = name
      this.pendingRect = rect ?? null
    },

    /** 确认打开 */
    confirm () {
      const target = this.pending
      this.pending = null
      this.pendingRect = null
      if (!target || target === 'login') { return }
      this[target] = true
    },

    /** 放弃打开 */
    cancel () {
      this.pending = null
      this.pendingRect = null
    }
  }
})

export { useOpenPanels }
