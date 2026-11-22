import { defineNuxtPlugin, useRouter } from '#app'
import { PiniaPluginContext, Store } from 'pinia'
import { useMain, flags } from '~~/stores/main'

interface BreakingChange {
  from?: string,
  to: string,
  reason: string[],
  affectedStores: string[]
}

const breakingChanges: BreakingChange[] = [
  {
    from: '1.0.0',
    to: '1.3.0',
    reason: [
      'Timer theme colours are now stored in a different way, restoring previous settings would cause the app to not have colours.'
    ],
    affectedStores: ['settings']
  },
  {
    from: '1.0.0',
    to: '1.4.0',
    reason: [
      'The settings\' theming data was restructured.'
    ],
    affectedStores: ['settings']
  },
  {
    from: '1.0.0',
    to: '1.4.1',
    reason: [
      'The app was rebranded to FocusTide.'
    ],
    affectedStores: ['tutorials']
  }
]

const persistStores = ['settings', 'tasklist', 'tutorials', 'main', 'garden', 'history']
const storeResetKey = '--reset-store'

/**
 * 各 store 持久化数据的迁移（在 $patch 之前、作用于原始 JSON）。
 *
 * 为什么必须在这一层：$patch 只合并「旧数据里存在的键」，而且数组是整体替换，
 * store 创建时又会先把默认 state 写回 localStorage —— 「字段缺失」这个信号
 * 在内存态里已经被默认值占位，在 state 层做的兜底永远不会触发。
 */
type StoreMigration = (raw: Record<string, any>) => Record<string, any>

const DEFAULT_UNLOCKED = ['maple', 'pine', 'cherry', 'oak']

const storeMigrations: Record<string, StoreMigration> = {
  garden: (raw) => {
    const next = { ...raw }

    // 老用户首次升级到「阳光」体系：把余额折算为 min(总分钟 x 30%, 300)
    if (next.legacyFolded === undefined && Number(next.totalMinutes) > 0) {
      const total = Math.round(Number(next.totalMinutes) || 0)
      const keep = Math.min(Math.round(total * 0.3), 300)
      next.spentSunlight = Math.max(0, total - keep)
      next.legacyFolded = true
    }

    // 已解锁物种：老数据没这个键 → 初始四件套；已有则补齐（老树不该变锁定）
    const unlocked = Array.isArray(next.unlocked) ? next.unlocked : []
    next.unlocked = Array.from(new Set([...unlocked, ...DEFAULT_UNLOCKED]))

    // 树：数组整体替换 → 逐棵补字段
    // 老树（没有 withered 字段）免疫枯萎；新树按自己的 immune 走
    next.trees = Array.isArray(next.trees)
      ? next.trees.map((tree: any) => ({
          ...tree,
          water: Number.isFinite(tree?.water) ? tree.water : 0,
          manual: typeof tree?.manual === 'boolean' ? tree.manual : false,
          immune: typeof tree?.immune === 'boolean' ? tree.immune : tree?.withered === undefined
        }))
      : []

    return next
  }
}

/** Get the persistence key of the store by its ID */
const getStorePersistenceKey = (id: string) => `persist-${id}`

/** Returns stores and reasons why they cannot be restored from previous versions
 * @example { settings: ['Something changed lately'] }
 */
function getBlockedStores (): Record<string, string[]> {
  const mainStore = localStorage.getItem(getStorePersistenceKey('main'))
  let previousVersion = '0.0.0'
  if (mainStore !== null) {
    const mainStoreParsed = JSON.parse(mainStore)

    previousVersion = mainStoreParsed.version
  }

  return persistStores.reduce((affectedStores, storeId) => {
    const storeExists = localStorage.getItem(getStorePersistenceKey(storeId)) !== null
    const breakingChangeIndex = breakingChanges.findIndex(breakingChange => breakingChange.affectedStores.includes(storeId) && breakingChange.to > previousVersion)

    if (storeExists && breakingChangeIndex >= 0) {
      affectedStores[storeId] = breakingChanges[breakingChangeIndex].reason
    }

    return affectedStores
  }, {} as Record<string, string[]>)
}

/** Restore store to its persisted state (if there is such a state) */
function restoreStore (store: Store) {
  const lsStore = localStorage.getItem(getStorePersistenceKey(store.$id))
  if (store === null) {
    return
  }

  let stateToRestore = JSON.parse(lsStore as string)

  // 迁移必须在 $patch 之前、且作用在原始 JSON 上
  const migrate = storeMigrations[store.$id]
  if (migrate && stateToRestore !== null && typeof stateToRestore === 'object') {
    stateToRestore = migrate(stateToRestore)
  }

  if (stateToRestore !== null) {
    onMounted(() => {
      store.$patch(stateToRestore)
    })

    const mainStore = useMain()
    mainStore.registerFlag(flags.STORE_RESTORED)
    mainStore.restoredStores.push(store.$id)
  }
}

export default defineNuxtPlugin(({ $pinia }) => {
  const router = useRouter()
  const blockedStores = getBlockedStores()
  //

  const PiniaPersistPlugin = ({ store }: PiniaPluginContext) => {
    // if (store.$id === 'main') {
    //   store.$patch({
    //     skippedStores: blockedStores
    //   })
    // }

    if (persistStores.includes(store.$id)) {
      const restore = localStorage.getItem(storeResetKey) == null

      // Restore the store first if it's not the main store (that contains the version number)
      if (restore && store.$id !== 'main') {
        // Check if the store can be restored
        if (Object.keys(blockedStores).includes(store.$id)) {
          console.warn(`Store '${store.$id}' was not be restored due to breaking changes that happened since the last app update: \n - ${blockedStores[store.$id].join('\n - ')}`)
        } else {
          restoreStore(store)
        }
      }

      const changeSubscription = () => {
        // Write initial state to storage
        localStorage.setItem(
          getStorePersistenceKey(store.$id),
          JSON.stringify(store.$state)
        )

        // Subscribe to changes and persist them
        const unsubscribe = store.$subscribe(() => {
          try {
            if (store.$id === 'settings') {
              if (store.$state.reset) {
                // if the settings store is in reset state, set store reset key
                localStorage.setItem(storeResetKey, '1')
              } else {
                // otherwise remove the reset key
                localStorage.removeItem(storeResetKey)
              }
            }

            // otherwise persist store
            localStorage.setItem(
              getStorePersistenceKey(store.$id),
              JSON.stringify(store.$state)
            )
          } catch (err) {
            console.log(err)
            // Failed to write to localStorage for some reason, unsubscribe persistence
            unsubscribe()
          }
        })
      }

      // `afterEach` is used as a workaround to Pinia subscribers disappearing on navigation
      changeSubscription()
      router.afterEach(changeSubscription)
    }
  }

  $pinia.use(PiniaPersistPlugin)
})
