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

export function useGardenCloud () {
  const auth = useAuth()
  const garden = useGarden()
  const runtimeConfig = useRuntimeConfig()

  const endpoint = computed(() => String(runtimeConfig.public.IDENTITY_API_GARDEN || ''))
  const enabled = computed(() => !!endpoint.value)

  let timer: ReturnType<typeof setTimeout> | null = null
  let suppressUntil = 0
  let inFlight = false

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
    if (!enabled.value || !auth.authenticated) { return }
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
        suppressUntil = Date.now() + SUPPRESS_AFTER_PULL
        garden.applyState(data.state)
      } else if (garden.treeCount > 0 || garden.totalMinutes > 0) {
        // 云端还没有 → 把本地的传上去（老用户第一次登录即上云）
        suppressUntil = Date.now() + SUPPRESS_AFTER_PULL
        await push()
      }
    } catch (err) {
      console.warn('garden load failed', err)
    }
  }

  // 登录状态变化 → 拉取
  watch(() => auth.authenticated, (value) => {
    if (value) { void pull() }
  })

  // 本地任何改动 → 防抖写回
  watch(() => garden.$state, schedulePush, { deep: true })

  return { pull, push }
}
