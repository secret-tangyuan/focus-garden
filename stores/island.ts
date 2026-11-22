import { defineStore } from 'pinia'

export type IslandTone = 'info' | 'success' | 'warning' | 'garden'

export interface IslandMessage {
  id: number
  title: string
  detail?: string
  tone: IslandTone
  duration: number
}

let nextId = 1

export const useIsland = defineStore('island', {
  state: () => ({
    current: null as IslandMessage | null
  }),

  actions: {
    show (message: Omit<IslandMessage, 'id' | 'duration'> & { duration?: number }) {
      this.current = {
        ...message,
        id: nextId++,
        duration: message.duration ?? 3200
      }
    },

    dismiss () {
      this.current = null
    }
  }
})
