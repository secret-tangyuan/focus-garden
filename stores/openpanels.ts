import { defineStore } from 'pinia'

const useOpenPanels = defineStore('openpanels', {
  state: () => ({
    settings: false,
    todo: false,
    garden: false
  })
})

export { useOpenPanels }
