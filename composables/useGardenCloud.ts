import { useAuth } from '~~/stores/auth'
import { useGarden } from '~~/stores/garden'

/**
 * 花园数据的云端同步
 *
 * 规则：
 *   - 未登录：数据只留在浏览器本地（localStorage），不上云、不发请求；
 *   - 已登录：以云端为准。登录后拉取云端存档；云端没有则把本地的传上去；
 *   - 本地任何改动都会防抖后写回云端，换设备登录即可接着种。
 */
const PUSH_DELAY = 1200
const SUPPRESS_AFTER_PULL = 800
const LOCAL_OWNER_KEY = 'focus-garden-cloud-owner'

export function useGardenCloud () {
  const auth = useAuth()
  const garden = useGarden()
  const runtimeConfig = useRuntimeConfig()

  const endpoint = computed(() => String(runtimeConfig.public.IDENTITY_API_GARDEN || ''))
  const enabled = computed(() => !!endpoint.value)
  const owner = computed(() => auth.user?.username ? `user:${auth.user.username}` : '')

  let timer: ReturnType<typeof setTimeout> | null = null
  let suppressUntil = 0
  let inFlight = false
  let pulling = false

  const localOwner = (): string => {
    if (!import.meta.client) { return '' }
    return localStorage.getItem(LOCAL_OWNER_KEY) || ''
  }

  const rememberOwner = (value: string) => {
    if (!import.meta.client || !value) { return }
    localStorage.setItem(LOCAL_OWNER_KEY, value)
  }

  const hasLocalGarden = (): boolean => {
    return garden.treeCount > 0 ||
      garden.sessions > 0 ||
      garden.totalMinutes > 0 ||
      garden.spentSunlight > 0
  }

  const push = async (): Promise<boolean> => {
    if (!enabled.value || !auth.authenticated || inFlight) { return false }
    inFlight = true
    try {
      const response = await fetch(endpoint.value, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ state: garden.exportState() })
      })
      if (!response.ok) {
        console.warn('garden sync failed', response.status)
        return false
      }
      return true
    } catch (err) {
      console.warn('garden sync failed', err)
      return false
    } finally {
      inFlight = false
    }
  }

  /** 防抖写回：连续改动只发最后一次 */
  const schedulePush = () => {
    if (!enabled.value || !auth.authenticated) { return }
    if (Date.now() < suppressUntil) { return }
    if (timer) { clearTimeout(timer) }
    timer = setTimeout(() => {
      timer = null
      void push()
    }, PUSH_DELAY)
  }

  /** 登录后拉取云端存档；云端为空则把本地的传上去 */
  const pull = async () => {
    if (!enabled.value || !auth.authenticated || !owner.value || pulling) { return }
    pulling = true
    // 拉取期间以及覆盖本地后的短窗口内，不允许 watcher 把旧本地状态回传。
    suppressUntil = Date.now() + 15000
    try {
      const response = await fetch(endpoint.value, {
        headers: { Accept: 'application/json' },
        credentials: 'include'
      })
      if (!response.ok) { return }
      const data = await response.json().catch(() => ({}))
      if (!data.ok) { return }

      if (data.state && typeof data.state === 'object') {
        // 云端为准：覆盖本地（刚拉下来的数据不再回传）
        garden.applyState(data.state)
        rememberOwner(owner.value)
      } else if (!localOwner() || localOwner() === owner.value) {
        // 云端还没有 → 把本地的传上去（老用户第一次登录即上云）
        rememberOwner(owner.value)
        if (hasLocalGarden()) { await push() }
      } else {
        // 同一浏览器换账号：上一位账号的本地数据绝不能写进新账号。
        garden.clearForest()
        rememberOwner(owner.value)
      }
    } catch (err) {
      console.warn('garden load failed', err)
    } finally {
      pulling = false
      suppressUntil = Date.now() + SUPPRESS_AFTER_PULL
    }
  }

  // 登录状态变化 → 拉取
  watch(() => [auth.authenticated, owner.value] as const, ([active, currentOwner]) => {
    if (!active) {
      if (timer) {
        clearTimeout(timer)
        timer = null
      }
      return
    }
    if (currentOwner) { void pull() }
  })

  // 本地任何改动 → 防抖写回
  watch(() => garden.$state, schedulePush, { deep: true })

  return { pull, push }
}
