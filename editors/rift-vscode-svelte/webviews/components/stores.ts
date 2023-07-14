import { writable } from 'svelte/store'
import type { SvelteStore } from '../../src/types'

export const DEFAULT_STATE: SvelteStore = {
  selectedAgentId: '',
  agents: {
  },
  availableAgents: []
};

// {
//   "rift-chat": {
//     type: "rift-chat",
//     chatHistory: [{ role: "assistant", content: "How can I help?" }],
//     tasks: { subtasks: [], task: { description: "Rift Chat", status: "running" } },
//   },
// }


export const state = writable<SvelteStore>(DEFAULT_STATE)
export const loading = writable(false)