import { writable } from 'svelte/store'
import type { SvelteStore } from '../../src/types'

export const DEFAULT_STATE: SvelteStore = {
  history: [],
  agents: [],
  logs: [],
};


export const state = writable(DEFAULT_STATE)
export const loading = writable(false)