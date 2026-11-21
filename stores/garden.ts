import { defineStore } from 'pinia'

/** 树种 */
export enum TreeSpecies {
  Maple = 'maple',
  Pine = 'pine',
  Cherry = 'cherry'
}

export interface Tree {
  /** 唯一 id */
  id: number
  /** 树种 */
  species: TreeSpecies
  /** 种下时的专注次数序号（用于计算成熟阶段） */
  bornAtSession: number
  /** 种下时累计专注分钟 */
  minutes: number
  /** 种下时间戳 */
  plantedAt: number
}

/** 树的生长阶段：0 树苗 → 3 成年 */
export type GrowthStage = 0 | 1 | 2 | 3

/** 每完成 N 次专注，森林里的树整体长大一级 */
const SESSIONS_PER_STAGE = 3

export const useGarden = defineStore('garden', {
  state: () => ({
    trees: [] as Tree[],
    /** 累计完成的专注段数 */
    sessions: 0,
    /** 累计专注分钟 */
    totalMinutes: 0,
    /** 最近一次种树的时间戳 */
    lastPlantedAt: 0,
    /** 最近一次专注的日期（YYYY-MM-DD），用于连续天数 */
    lastSessionDay: '',
    /** 连续专注天数 */
    streak: 0
  }),

  getters: {
    treeCount: state => state.trees.length,

    /** 今日已专注分钟 */
    todayMinutes: state => {
      const today = new Date().toISOString().slice(0, 10)
      return state.trees.filter(tree => new Date(tree.plantedAt).toISOString().slice(0, 10) === today)
        .reduce((sum, tree) => sum + tree.minutes, 0)
    },

    /** 森林中的树（最新种的排在前面） */
    forest: state => [...state.trees].sort((a, b) => b.plantedAt - a.plantedAt),

    /** 树种分布 */
    speciesCount: state => {
      const counts: Record<string, number> = {}
      for (const tree of state.trees) {
        counts[tree.species] = (counts[tree.species] ?? 0) + 1
      }
      return counts
    }
  },

  actions: {
    /** 计算某棵树的生长阶段 */
    stageOf (tree: Tree): GrowthStage {
      const grown = this.sessions - tree.bornAtSession
      const stage = Math.floor(grown / SESSIONS_PER_STAGE)
      return Math.max(0, Math.min(3, stage)) as GrowthStage
    },

    /** 记录一次完成的专注，并种下一棵树 */
    plantTree (minutes: number) {
      const rounded = Math.max(1, Math.round(minutes))
      const order: TreeSpecies[] = [TreeSpecies.Maple, TreeSpecies.Pine, TreeSpecies.Cherry]
      const species = order[this.trees.length % order.length]

      const tree: Tree = {
        id: Date.now() + Math.floor(Math.random() * 1000),
        species,
        bornAtSession: this.sessions,
        minutes: rounded,
        plantedAt: Date.now()
      }

      this.trees.push(tree)
      this.sessions += 1
      this.totalMinutes += rounded
      this.lastPlantedAt = tree.plantedAt

      // 连续天数
      const today = new Date().toISOString().slice(0, 10)
      if (this.lastSessionDay !== today) {
        const yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10)
        this.streak = this.lastSessionDay === yesterday ? this.streak + 1 : 1
        this.lastSessionDay = today
      }

      return tree
    },

    /** 清空森林 */
    clearForest () {
      this.trees = []
      this.sessions = 0
      this.totalMinutes = 0
      this.streak = 0
      this.lastSessionDay = ''
      this.lastPlantedAt = 0
    }
  }
})
