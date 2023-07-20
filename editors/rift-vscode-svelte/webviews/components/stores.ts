import { writable } from 'svelte/store'
import type { WebviewState } from '../../src/types'

export const DEFAULT_STATE: WebviewState = {
  selectedAgentId: '',
  agents: {
  },
  availableAgents: [{
    agent_type: "rift_chat",
    agent_description: '',
    agent_icon: '',
    display_name: 'Rift Chat'
  }]
};

// {
//   "rift-chat": {
//     type: "rift-chat",
//     chatHistory: [{ role: "assistant", content: "How can I help?" }],
//     tasks: { subtasks: [], task: { description: "Rift Chat", status: "running" } },
//   },
// }


export const dropdownOpen = writable(false)
export const state = writable<WebviewState>(DEFAULT_STATE)
export const loading = writable(false)
export const progressResponse = writable('')