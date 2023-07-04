import {writable} from 'svelte/store'
import type {SvelteStore} from '../../src/types'

const DEFAULT_STATE:SvelteStore = {
  history: [],
};

const LOG_STATE = {
  logs: [],
};

export const state = writable(DEFAULT_STATE)
export const logs = writable(LOG_STATE)
export const loading = writable(false)