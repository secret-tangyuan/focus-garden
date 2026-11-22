import { defineStore } from 'pinia'

/**
 * 物种表（移植自 FocusGrove，MIT License, Copyright (c) 2026 FocusGrove contributors）
 * https://github.com/haminyovanantonyfk-netizen/focus-grove
 * 原实现：app.js 的 SPECIES 表。id / 造型 / 主色沿用上游，解锁价按本站玩法调整。
 */
export type PlantSpecies =
  | 'maple' | 'pine' | 'cherry' | 'oak' | 'bamboo' | 'sunflower'
  | 'palm' | 'cactus' | 'willow' | 'lavender' | 'bonsai' | 'sequoia'

export type PlantShape = 'round' | 'pine' | 'bamboo' | 'flower' | 'palm' | 'cactus' | 'willow'

export interface PlantInfo {
  /** 造型类型（决定 SVG 画法） */
  shape: PlantShape
  /** 主色 / 次色 */
  c1: string
  c2: string
  /** 解锁价（阳光）；0 = 初始解锁 */
  cost: number
}

export const PLANT_SPECIES: Record<PlantSpecies, PlantInfo> = {
  maple: { shape: 'round', c1: '#ea580c', c2: '#f97316', cost: 0 },
  pine: { shape: 'pine', c1: '#15803d', c2: '#166534', cost: 0 },
  cherry: { shape: 'round', c1: '#f472b6', c2: '#f9a8d4', cost: 0 },
  oak: { shape: 'round', c1: '#16a34a', c2: '#22c55e', cost: 0 },
  bamboo: { shape: 'bamboo', c1: '#4d7c0f', c2: '#65a30d', cost: 30 },
  sunflower: { shape: 'flower', c1: '#eab308', c2: '#facc15', cost: 40 },
  palm: { shape: 'palm', c1: '#65a30d', c2: '#84cc16', cost: 60 },
  cactus: { shape: 'cactus', c1: '#16a34a', c2: '#4ade80', cost: 80 },
  willow: { shape: 'willow', c1: '#65a30d', c2: '#a3e635', cost: 100 },
  lavender: { shape: 'flower', c1: '#a855f7', c2: '#c084fc', cost: 130 },
  bonsai: { shape: 'round', c1: '#15803d', c2: '#86efac', cost: 180 },
  sequoia: { shape: 'pine', c1: '#166534', c2: '#14532d', cost: 250 }
}

export const SPECIES_ORDER: PlantSpecies[] = [
  'maple', 'pine', 'cherry', 'oak', 'bamboo', 'sunflower',
  'palm', 'cactus', 'willow', 'lavender', 'bonsai', 'sequoia'
]

/** 初始解锁的物种 */
export const DEFAULT_UNLOCKED: PlantSpecies[] = ['maple', 'pine', 'cherry', 'oak']

/** 手动种一棵树的价（阳光） */
export const PLANT_COST = 40
/** 浇水价（阳光）：按当前形态递增 */
export const WATER_COST = [10, 20, 30, 40]
/** 每棵树最多浇几次 */
export const WATER_LIMIT = 2
/** 自然成长：每 N 段专注 +1 形态 */
export const SESSIONS_PER_STAGE = 2
/** 最高形态 */
export const MAX_STAGE = 4
/** 连续多少天没登录且没专注 → 枯萎 */
export const WITHER_DAYS = 7
/** 扩建花园的价（阳光） */
export const EXPAND_COST = [150, 400, 900, 1600]
/** 各档位对应的地块容量 */
export const PLOT_CAPACITY = [30, 60, 120, 240, 400]

export interface Tree {
  /** 唯一 id */
  id: number
  /** 树种 */
  species: PlantSpecies
  /** 种下时的专注次数序号（自然成长基准） */
  bornAtSession: number
  /** 种下时累计专注分钟 */
  minutes: number
  /** 种下时间戳 */
  plantedAt: number
  /** 浇灌次数（老数据无此字段，读时 ?? 0） */
  water?: number
  /** 是否是用阳光手动种下的 */
  manual?: boolean
  /** 老用户已有的树：免疫枯萎 */
  immune?: boolean
  /** 是否已枯萎 */
  withered?: boolean
}

/** 形态：0 种子 → 4 长成 */
export type GrowthStage = 0 | 1 | 2 | 3 | 4

export const useGarden = defineStore('garden', {
  state: () => ({
    trees: [] as Tree[],
    /** 累计完成的专注段数 */
    sessions: 0,
    /** 累计专注分钟（同时是阳光的产出总额） */
    totalMinutes: 0,
    /** 已消耗的阳光（账本；余额 = totalMinutes - spentSunlight） */
    spentSunlight: 0,
    /** 已解锁的物种 */
    unlocked: [...DEFAULT_UNLOCKED] as PlantSpecies[],
    /** 扩建档位 */
    plotLevel: 0,
    /** 最近一次登录或完成专注的时间戳（枯萎判定用） */
    lastTendAt: 0,
    /** 老用户折算是否已执行（老数据没有这个键 → 迁移时折算一次） */
    legacyFolded: true,
    /** 最近一次种树的时间戳 */
    lastPlantedAt: 0,
    /** 最近一次专注的日期（YYYY-MM-DD），用于连续天数 */
    lastSessionDay: '',
    /** 连续专注天数 */
    streak: 0
  }),

  getters: {
    /** 可用阳光（余额）：1 阳光 = 1 专注分钟 */
    sunlight: (state) => Math.max(0, state.totalMinutes - state.spentSunlight),

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
    },

    /** 最近一次种下的那棵树对应的专注分钟（= 本次获得的阳光） */
    lastPlantedMinutes: state => {
      if (!state.lastPlantedAt) { return 0 }
      const tree = state.trees.find(item => item.plantedAt === state.lastPlantedAt)
      return tree ? tree.minutes : 0
    },

    /** 当前地块容量 */
    plotCapacity: state => PLOT_CAPACITY[Math.min(state.plotLevel, PLOT_CAPACITY.length - 1)],

    /** 距离下次扩建的价格（已满级返回 null） */
    nextExpandCost: state => state.plotLevel < EXPAND_COST.length ? EXPAND_COST[state.plotLevel] : null,

    /** 距离枯萎还剩几天（用于提示） */
    daysToWither: state => {
      if (!state.lastTendAt) { return WITHER_DAYS }
      const idle = (Date.now() - state.lastTendAt) / 86400000
      return Math.max(0, Math.ceil(WITHER_DAYS - idle))
    }
  },

  actions: {
    /** 某棵树的形态（老数据的 water 是 undefined，必须 ?? 0） */
    stageOf (tree: Tree): GrowthStage {
      const water = tree.water ?? 0
      const grown = this.sessions - tree.bornAtSession
      const stage = Math.floor(grown / SESSIONS_PER_STAGE) + water
      if (!Number.isFinite(stage)) { return 0 }
      return Math.max(0, Math.min(MAX_STAGE, stage)) as GrowthStage
    },

    /** 浇一次水的价（按当前形态递增） */
    waterCostOf (tree: Tree): number {
      return WATER_COST[Math.min(this.stageOf(tree), WATER_COST.length - 1)]
    },

    /** 能不能再浇这棵树（次数上限） */
    canWater (tree: Tree): boolean {
      return (tree.water ?? 0) < WATER_LIMIT
    },

    /** 自动轮换：优先用还没出现过的已解锁物种 */
    nextSpecies (): PlantSpecies {
      const pool = this.unlocked.length > 0 ? this.unlocked : DEFAULT_UNLOCKED
      const unused = pool.filter(id => !this.trees.some(tree => tree.species === id))
      const list = unused.length > 0 ? unused : pool
      return list[this.trees.length % list.length]
    },

    /** 完成一段专注：发阳光 + 自动种一棵树 */
    completeFocus (minutes: number) {
      const rounded = Math.max(1, Math.round(minutes))
      const species = this.nextSpecies()
      const tree: Tree = {
        id: Date.now() + Math.floor(Math.random() * 1000),
        species,
        bornAtSession: this.sessions,
        minutes: rounded,
        plantedAt: Date.now(),
        water: 0,
        manual: false,
        withered: false
      }
      this.trees.push(tree)
      this.sessions += 1
      this.totalMinutes += rounded
      this.lastPlantedAt = tree.plantedAt
      this.lastTendAt = Date.now()

      // 连续天数
      const today = new Date().toISOString().slice(0, 10)
      if (this.lastSessionDay !== today) {
        const yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10)
        this.streak = this.lastSessionDay === yesterday ? this.streak + 1 : 1
        this.lastSessionDay = today
      }

      return tree
    },

    /** 用阳光手动种一棵树（自选树种，起始形态 1） */
    plantManual (species: PlantSpecies): Tree | null {
      if (!this.unlocked.includes(species)) { return null }
      if (this.sunlight < PLANT_COST) { return null }
      if (this.trees.length >= this.plotCapacity) { return null }

      const tree: Tree = {
        id: Date.now() + Math.floor(Math.random() * 1000),
        species,
        // 起始形态 1：等价于「2 段专注前就种下」
        bornAtSession: this.sessions - SESSIONS_PER_STAGE,
        minutes: 0,
        plantedAt: Date.now(),
        water: 0,
        manual: true,
        withered: false
      }
      this.spentSunlight += PLANT_COST
      this.trees.push(tree)
      this.lastPlantedAt = tree.plantedAt
      this.lastTendAt = Date.now()
      return tree
    },

    /** 浇一次水：花阳光，形态 +1；已枯萎的树浇水即复活 */
    waterTree (treeId: number): boolean {
      const tree = this.trees.find(item => item.id === treeId)
      if (!tree) { return false }
      if (!this.canWater(tree)) { return false }
      const cost = this.waterCostOf(tree)
      if (this.sunlight < cost) { return false }

      this.spentSunlight += cost
      tree.water = (tree.water ?? 0) + 1
      if (tree.withered) {
        tree.withered = false
      }
      this.lastTendAt = Date.now()
      return true
    },

    /** 解锁一个物种 */
    unlockSpecies (species: PlantSpecies): boolean {
      if (this.unlocked.includes(species)) { return false }
      const info = PLANT_SPECIES[species]
      if (!info) { return false }
      if (this.sunlight < info.cost) { return false }
      this.spentSunlight += info.cost
      this.unlocked.push(species)
      this.lastTendAt = Date.now()
      return true
    },

    /** 扩建花园：提高地块容量 */
    expandGarden (): boolean {
      const cost = this.nextExpandCost
      if (cost === null) { return false }
      if (this.sunlight < cost) { return false }
      this.spentSunlight += cost
      this.plotLevel += 1
      this.lastTendAt = Date.now()
      return true
    },

    /**
     * 枯萎检查：连续 WITHER_DAYS 天既没登录也没完成专注 → 树枯萎。
     * 老用户已有的树（immune）不枯萎。
     */
    checkWither (): boolean {
      if (!this.lastTendAt) {
        this.lastTendAt = Date.now()
        return false
      }
      const idleDays = (Date.now() - this.lastTendAt) / 86400000
      if (idleDays < WITHER_DAYS) { return false }

      let changed = false
      for (const tree of this.trees) {
        if (tree.immune) { continue }
        if (tree.withered) { continue }
        tree.withered = true
        changed = true
      }
      return changed
    },

    /** 导出可上云的快照（只含可序列化的纯数据） */
    exportState () {
      return {
        v: 1,
        trees: this.trees.slice(0, 500),
        sessions: this.sessions,
        totalMinutes: this.totalMinutes,
        spentSunlight: this.spentSunlight,
        unlocked: this.unlocked.slice(),
        plotLevel: this.plotLevel,
        streak: this.streak,
        lastSessionDay: this.lastSessionDay,
        lastPlantedAt: this.lastPlantedAt,
        lastTendAt: this.lastTendAt
      }
    },

    /** 用云端快照覆盖本地（登录后以云端为准；未登录时根本不会走到这里） */
    applyState (state: unknown): boolean {
      if (!state || typeof state !== 'object') { return false }
      const raw = state as Record<string, any>

      const trees = Array.isArray(raw.trees) ? raw.trees : []
      this.trees = trees.map((tree: any) => ({
        ...tree,
        water: Number.isFinite(tree?.water) ? tree.water : 0,
        manual: tree?.manual === true,
        immune: tree?.immune === true,
        withered: tree?.withered === true
      }))

      this.sessions = Math.max(0, Math.round(Number(raw.sessions) || 0))
      this.totalMinutes = Math.max(0, Math.round(Number(raw.totalMinutes) || 0))
      this.spentSunlight = Math.max(0, Math.round(Number(raw.spentSunlight) || 0))
      this.unlocked = Array.isArray(raw.unlocked) && raw.unlocked.length
        ? raw.unlocked.filter((id: any) => typeof id === 'string')
        : [...DEFAULT_UNLOCKED]
      this.plotLevel = Math.max(0, Math.round(Number(raw.plotLevel) || 0))
      this.streak = Math.max(0, Math.round(Number(raw.streak) || 0))
      this.lastSessionDay = String(raw.lastSessionDay || '')
      this.lastPlantedAt = Math.max(0, Math.round(Number(raw.lastPlantedAt) || 0))
      this.lastTendAt = Math.max(0, Math.round(Number(raw.lastTendAt) || Date.now()))
      return true
    },

    /** 记录一次登录（登录也算「打理花园」，重置枯萎倒计时） */
    touchByLogin () {
      this.lastTendAt = Date.now()
    },

    /** 清空森林（全重置） */
    clearForest () {
      this.trees = []
      this.sessions = 0
      this.totalMinutes = 0
      this.spentSunlight = 0
      this.unlocked = [...DEFAULT_UNLOCKED]
      this.plotLevel = 0
      this.streak = 0
      this.lastSessionDay = ''
      this.lastPlantedAt = 0
      this.lastTendAt = Date.now()
    }
  }
})
