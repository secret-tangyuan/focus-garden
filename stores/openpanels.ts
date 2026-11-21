import { defineStore } from 'pinia'

export type PanelName = 'settings' | 'todo' | 'garden'

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
    pending: null as PanelName | null,
    /** 触发按钮的位置（小窗贴着它显示） */
    pendingRect: null as TriggerRect | null
  }),

  actions: {
    /** 请求打开面板：先在按钮旁提示一次 */
    request (name: PanelName, rect?: TriggerRect) {
      if (this[name]) {
        // 已经打开 → 直接关闭
        this[name] = false
        return
      }
      this.pending = name
      this.pendingRect = rect ?? null
    },

    /** 确认打开 */
    confirm () {
      if (!this.pending) { return }
      this[this.pending] = true
      this.pending = null
      this.pendingRect = null
    },

    /** 放弃打开 */
    cancel () {
      this.pending = null
      this.pendingRect = null
    }
  }
})

export { useOpenPanels }
