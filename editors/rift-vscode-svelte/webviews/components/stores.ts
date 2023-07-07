import { writable } from 'svelte/store'
import type { SvelteStore } from '../../src/types'

export const DEFAULT_STATE: SvelteStore = {
  currentlySelectedAgentId: 'rift-chat',
  agents: {
    "rift-chat": {
      chatHistory: [],
      logs: []
    }
  }
  // logs: [],
};


export const state = writable<SvelteStore>(DEFAULT_STATE)
export const loading = writable(false)