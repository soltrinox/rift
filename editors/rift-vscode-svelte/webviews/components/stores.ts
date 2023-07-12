import { writable } from 'svelte/store'
import type { SvelteStore } from '../../src/types'

export const DEFAULT_STATE: SvelteStore = {
  selectedAgentId: '',
  agents: {
  },
  availableAgents: []
};


export const state = writable<SvelteStore>(DEFAULT_STATE)
export const loading = writable(false)