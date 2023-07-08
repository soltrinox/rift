import { writable } from 'svelte/store'
import type { SvelteStore } from '../../src/types'

export const DEFAULT_STATE: SvelteStore = {
  selectedAgentId: 'rift-chat',
  agents: {
    "deadb33f": {
      id: "deadb33f",
      type: "rift-chat",
      chatHistory: [{ role: "assistant", content: "How can I help?" }],
      taskRoot: [],
    },
    "cafebabe": {
      id: "cafebabe",
      type: "aider",
      chatHistory: [{ role: "assistant", content: "How can I aid?" }],
      taskRoot: [],
    }
  }
};


export const state = writable<SvelteStore>(DEFAULT_STATE)
export const loading = writable(false)