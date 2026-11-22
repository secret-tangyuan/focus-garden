import { reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

import { useSettings } from '~~/stores/settings'
import { useSchedule } from '~~/stores/schedule'
import { useNotifications } from '~~/stores/notifications'
import { EventType, useEvents } from '~~/stores/events'
import { useGarden } from '~~/stores/garden'
import { useHistory } from '~~/stores/history'

interface SoundSettings {
  source: HTMLAudioElement,
  ready: boolean
}

export function useWeb () {
  const settingsStore = useSettings()
  const scheduleStore = useSchedule()
  const notificationsStore = useNotifications()
  const eventsStore = useEvents()
  const gardenStore = useGarden()
  const historyStore = useHistory()
  const i18n = useI18n()

  const state = reactive({
    currentSoundSet: null as string | null,
    sounds: {
      work: null as SoundSettings | null,
      shortpause: null as SoundSettings | null,
      longpause: null as SoundSettings | null
    }
  })

  const lastEvent = computed(() => {
    const lastEventArray = eventsStore.events.slice(-1)
    return lastEventArray.length > 0 ? lastEventArray[0] : null
  })

  /** 找到最近一次「开始计时」的时间，作为本次专注的起点 */
  const findLastStartTime = (): number => {
    const startEvent = [...eventsStore.events].reverse().find(event => event._event === EventType.TIMER_START)
    const timestamp = startEvent?._timestamp?.getTime()
    return timestamp ?? (Date.now() - (scheduleStore.getSchedule[0].length ?? 0))
  }

  watch(lastEvent, (newValue) => {
    if (newValue === null) { return }

    if (newValue._event === EventType.TIMER_FINISH) {
      showNotification(scheduleStore.getSchedule[1].type)

      // 完成一段专注 → 种下一棵树，并写入专注记录
      const finishedItem = scheduleStore.getSchedule[0]
      if (finishedItem.type === 'work') {
        const minutes = Math.round((finishedItem.length ?? 0) / 60000)
        // 完成一段专注：发阳光（1 分钟 = 1 阳光）+ 自动种一棵树
        gardenStore.completeFocus(minutes)
        historyStore.recordFocus(findLastStartTime(), minutes, true)
      }
    }

    if (newValue._event === EventType.TIMER_STOP) {
      // 中途放弃（已专注 ≥1 分钟才记录）
      const elapsed = Math.floor((scheduleStore.getSchedule[0].timeElapsed ?? 0) / 60000)
      if (elapsed >= 1) {
        historyStore.recordFocus(findLastStartTime(), elapsed, false)
      }
    }
  })

  watch(() => settingsStore.audio.soundSet, (newSoundSet) => {
    loadSoundSet(newSoundSet)
  })

  eventsStore.$subscribe(() => {
    if (eventsStore.lastEvent !== null && eventsStore.lastEvent._event === EventType.NOTIFICATIONS_ENABLED && window.Notification && window.Notification.permission === 'default') {
      window.Notification.requestPermission().then((newNotificationPermission) => {
        settingsStore.$patch({
          permissions: {
            notifications: newNotificationPermission === 'granted'
          }
        })
      })
    }
  })

  onMounted(() => {
    // Register app started notification
    eventsStore.recordEvent(EventType.APP_STARTED)

    loadSoundSet(settingsStore.audio.soundSet)

    // Check Visibility and register in store
    if (window && window.document && 'hidden' in window.document) {
      window.document.addEventListener('visibilitychange', () => {
        settingsStore.registerNewHidden(window.document.hidden)
      }, false)

      // Commit this information immediately to make sure it's up to date
      settingsStore.registerNewHidden(window.document.hidden)
    } else {
      settingsStore.registerNewHidden(false)
    }

    // Check permissions
    notificationsStore.updateEnabled()
  })

  /**
  * Load a sound set into memory
  * @param {String} setName Name of the sound set to load
  */
  const loadSoundSet = (setName = settingsStore.audio.soundSet) => {
    if (state.currentSoundSet === setName) { return }

    try {
      for (const key in state.sounds) {
        const soundKey = key as keyof typeof state.sounds
        const newSound = {
          source: new Audio(`/audio/${setName}/${key}.mp3`),
          ready: false
        }

        newSound.source.addEventListener('canplay', () => {
          newSound.ready = true
        })

        state.sounds[soundKey] = newSound
      }

      state.currentSoundSet = setName
    } catch (err) {
      console.warn(err)
    }
  }

  /**
   * Play the specified sound
   * @param {String} key The key of the sound. Valid values are `work`, `pause` and `longpause`.
   */
  const playSound = (key: keyof typeof state.sounds) => {
    // load sound set if not already loaded
    if (!state.currentSoundSet) {
      loadSoundSet(settingsStore.audio.soundSet)
    }

    if (state.sounds[key] !== null && settingsStore.permissions.audio) {
      state.sounds[key]!.source.volume = settingsStore.audio.volume
      state.sounds[key]?.source.play()
    }
  }

  const showNotification = (nextState: keyof typeof state.sounds) => {
    playSound(nextState)

    // TODO Firefox does not support actions
    if (window.Notification.permission !== 'granted' || settingsStore.permissions.notifications !== true) { return }
    const notificationActions : NotificationAction[] = []
    if (nextState === 'work') {
      notificationActions.push({
        action: 'ready',
        title: i18n.t('notification.action.ready')
      })
    }

    try {
      new Notification(i18n.t('notification.' + nextState + '.title'), { // eslint-disable-line no-new
        tag: 'FocusTide-SectionNotify',
        body: i18n.t('notification.' + nextState + '.body'),
        actions: notificationActions
      })
    } catch (err) {
      console.warn(err)
    }
  }
}
