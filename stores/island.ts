import { defineStore } from 'pinia'
import { Section } from './settings'
import { TimerState, useSchedule } from './schedule'

export type IslandTone = 'info' | 'success' | 'warning' | 'garden'

/** 专注中的处理方式：
 *  critical —— 关键通知，专注中也立刻显示
 *  defer    —— 非关键通知，专注中暂存，专注结束后补发
 *  silent   —— 冗余反馈，专注中直接不显示
 */
export type IslandFocusMode = 'critical' | 'defer' | 'silent'

export interface IslandMessage {
  id: number
  title: string
  detail?: string
  tone: IslandTone
  duration: number
}

export interface IslandRequest {
  title: string
  detail?: string
  tone?: IslandTone
  duration?: number
  focus?: IslandFocusMode
}

let nextId = 1

/** 实时判断是否正处于专注工作段（发通知的瞬间直接读计时状态，避免 watch 滞后） */
const isFocusingNow = (): boolean => {
  const schedule = useSchedule()
  return schedule.currentSectionType === Section.work && schedule.timerState === TimerState.RUNNING
}

export const useIsland = defineStore('island', {
  state: () => ({
    /** 当前显示的通知 */
    current: null as IslandMessage | null,
    /** 专注中暂存的通知（专注结束后补发） */
    deferred: null as IslandMessage | null,
    /** 是否正处于专注工作段（工作段且计时在跑） */
    focusing: false
  }),

  actions: {
    /** 切换「是否专注中」；离开专注时补发暂存的通知 */
    setFocusing (value: boolean) {
      if (this.focusing === value) { return }
      this.focusing = value
      if (!value) { this.flushDeferred() }
    },

    show (request: IslandRequest) {
      const mode = request.focus ?? 'critical'
      // 只用实时状态判断，避免 watch 滞后导致「暂停后仍算专注中」
      const focusing = isFocusingNow()
      if (focusing && mode === 'silent') { return }

      const message: IslandMessage = {
        id: nextId++,
        title: request.title,
        detail: request.detail,
        tone: request.tone ?? 'info',
        duration: request.duration ?? 3200
      }

      if (focusing && mode === 'defer') {
        // 专注中不打扰：只保留最后一条，专注结束后再补发
        this.deferred = message
        return
      }

      this.current = message
      if (mode === 'critical') { this.deferred = null }
    },

    /** 补发暂存的通知 */
    flushDeferred () {
      if (!this.deferred) { return }
      const message = this.deferred
      this.deferred = null
      this.current = message
    },

    dismiss () {
      this.current = null
    }
  }
})
