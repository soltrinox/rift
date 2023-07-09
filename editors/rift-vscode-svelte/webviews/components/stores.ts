import { writable } from 'svelte/store'
import type { SvelteStore } from '../../src/types'

export const DEFAULT_STATE: SvelteStore = {
  selectedAgentId: 'deadb33f2',
  agents: {
    "deadb33f2": {
      id: "deadb33f2",
      type: "rift-chat",
      chatHistory: [{ role: "assistant", content: "How can I help?" }],
      taskRoot: [],
    },
    "cafebabe": {
      id: "cafebabe",
      type: "aider",
      chatHistory: [{ role: "assistant", content: "How can I aid?" }],
      taskRoot: [],
    },
    "abcdef": {
      id: "abcdef",
      type: "aider",
      chatHistory: [{ role: "assistant", content: "How can I aid?" }],
      taskRoot: [],
    }
  },
  availableAgents: []
};


export const state = writable<SvelteStore>(DEFAULT_STATE)
export const loading = writable(false)