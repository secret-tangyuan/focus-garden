import { defineStore } from 'pinia'

export interface FocusRecord {
  /** 唯一 id */
  id: number
  /** 开始时间戳 */
  startedAt: number
  /** 结束时间戳 */
  endedAt: number
  /** 专注时长（分钟） */
  minutes: number
  /** 是否完整完成（未中途放弃） */
  completed: boolean
}

export interface LoginRecord {
  /** 唯一 id */
  id: number
  /** 登录时间戳 */
  at: number
}

export const useHistory = defineStore('history', {
  state: () => ({
    /** 专注记录 */
    records: [] as FocusRecord[],
    /** 登录记录 */
    logins: [] as LoginRecord[]
  }),

  getters: {
    /** 最近的登录记录 */
    recentLogins: state => [...state.logins].sort((a, b) => b.at - a.at),
    /** 最近的专注记录 */
    recentRecords: state => [...state.records].sort((a, b) => b.startedAt - a.startedAt),
    /** 最近 7 天的每日专注分钟数（用于小柱状图） */
    weeklyMinutes: state => {
      const days: { day: string, label: string, minutes: number }[] = []
      const now = new Date()

      for (let i = 6; i >= 0; i--) {
        const date = new Date(now.getTime() - i * 86400000)
        const key = date.toISOString().slice(0, 10)
        const minutes = state.records
          .filter(record => new Date(record.startedAt).toISOString().slice(0, 10) === key)
          .reduce((sum, record) => sum + record.minutes, 0)
        days.push({ day: key, label: `${date.getMonth() + 1}/${date.getDate()}`, minutes })
      }

      return days
    }
  },

  actions: {
    /** 记录一次登录（进入专注模式） */
    recordLogin () {
      this.logins.push({ id: Date.now(), at: Date.now() })
      if (this.logins.length > 200) { this.logins.splice(0, this.logins.length - 200) }
    },

    /** 记录一次专注 */
    recordFocus (startedAt: number, minutes: number, completed: boolean) {
      this.records.push({
        id: Date.now() + Math.floor(Math.random() * 1000),
        startedAt,
        endedAt: Date.now(),
        minutes: Math.max(1, Math.round(minutes)),
        completed
      })
      if (this.records.length > 500) { this.records.splice(0, this.records.length - 500) }
    },

    /** 清空记录 */
    clearHistory () {
      this.records = []
      this.logins = []
    }
  }
})
