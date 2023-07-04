import {writable} from 'svelte/store'

const DEFAULT_STATE = {
  history: [],
};
export const state = writable(DEFAULT_STATE)
export const loading = writable(false)