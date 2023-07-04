import { writable } from 'svelte/store'

const DEFAULT_STATE = {
  history: [],
};

const LOG_STATE = {
  logs: [],
};

export const state = writable(DEFAULT_STATE)
export const logs = writable(LOG_STATE)
export const loading = writable(false)