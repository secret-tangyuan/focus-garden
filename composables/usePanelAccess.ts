import { useOpenPanels, type PanelName, type TriggerRect } from '~~/stores/openpanels'
import { TimerState, useSchedule } from '~~/stores/schedule'
import { Section } from '~~/stores/settings'
import { useAuth } from '~~/stores/auth'

export type AccessTarget = PanelName | 'login'

/**
 * 设置 / 森林 / 登录 的打开入口
 * - 任何时候都能打开
 * - 只有专注进行中（计时在跑）时才先弹一次二次确认
 */
export function usePanelAccess () {
  const openPanels = useOpenPanels()
  const scheduleStore = useSchedule()
  const auth = useAuth()
  const runtimeConfig = useRuntimeConfig()

  /**
   * 「专注进行中」= 计时器在跑 且 当前段是 work 段。
   *
   * 判定来源：scheduleStore.currentSectionType
   * - 开始计时时由 lockInfo 锁定（components/ticker.ts）
   * - Skip 模式推进时由 scheduleStore.advance() 锁定（stores/schedule.ts）
   * - 暂停 / 停止 / 未开始 → timerState 不是 RUNNING → 不提示
   * - 休息段（shortpause / longpause）→ 不提示
   *
   * 取不到类型时一律当作「不是专注」：宁可少弹一次提示，也不要在休息段误弹。
   */
  const isFocusing = computed(() => {
    if (scheduleStore.timerState !== TimerState.RUNNING) { return false }
    return scheduleStore.currentSectionType === Section.work
  })

  /** 身份中心地址（构建期注入，不写死域名） */
  const authBaseUrl = computed(() => String(runtimeConfig.public.AUTH_BASE_URL || '').replace(/\/$/, ''))

  /** 登录地址：带 next 回跳到本站 */
  const loginUrl = () => {
    if (!import.meta.client) { return '' }
    const back = `${location.origin}${location.pathname}`
    return `${authBaseUrl.value}/login?next=${encodeURIComponent(back)}`
  }

  /** 在新标签页打开登录（不加 noopener，统一身份靠 opener 回传） */
  const openLoginTab = () => {
    if (!import.meta.client) { return }
    const url = loginUrl()
    if (!url) { return }
    window.open(url, '_blank')
  }

  /**
   * 打开面板 / 登录
   * @param target 目标面板或登录
   * @param rect 触发按钮位置（专注中弹小窗时贴着它显示）
   */
  const requestAccess = (target: AccessTarget, rect?: TriggerRect) => {
    if (target !== 'login' && openPanels[target]) {
      // 已经打开 → 直接关闭
      openPanels[target] = false
      return
    }

    if (isFocusing.value) {
      // 专注中：先在小窗里确认一次
      openPanels.request(target, rect)
      return
    }

    if (target === 'login') {
      // 站内精简版登录（按钮旁的小窗）
      auth.openLogin(rect)
      return
    }

    openPanels[target] = true
  }

  /** 确认打开（处理登录这种非面板的目标） */
  const confirmAccess = () => {
    const target = openPanels.pending

    if (target === 'login') {
      const rect = openPanels.pendingRect
      openPanels.cancel()
      auth.openLogin(rect)
      return
    }

    openPanels.confirm()
  }

  return { isFocusing, requestAccess, confirmAccess, openLoginTab, loginUrl }
}
