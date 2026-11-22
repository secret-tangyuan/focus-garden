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
    pendingRect: null as TriggerRect | null,
    /** 面板从哪个按钮展开，关闭时也回到这里 */
    panelRect: {
      settings: null,
      todo: null,
      garden: null
    } as Record<PanelName, TriggerRect | null>
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
      const rect = this.pendingRect
      this.pending = null
      this.pendingRect = null
      if (!target || target === 'login') { return }
      this.panelRect[target] = rect
      this[target] = true
    },

    /** 放弃打开 */
    cancel () {
      this.pending = null
      this.pendingRect = null
    },

    /** 记录触发按钮，供展开 / 收回动画使用 */
    remember (name: PanelName, rect?: TriggerRect) {
      this.panelRect[name] = rect ?? null
    },

    /** 关闭所有辅助面板 */
    closeAll () {
      this.settings = false
      this.todo = false
      this.garden = false
    }
  }
})

export { useOpenPanels }
