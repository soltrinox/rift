import { readable, writable } from 'svelte/store'
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

export const state = readable<WebviewState>(DEFAULT_STATE, (set) => {
  window.addEventListener('message', (event:any) => {
    if(event.data.type != 'stateUpdate') throw new Error('Message passed to webview that is not stateUpdate')
    const newState = event.data.data as WebviewState
    set(newState)
  })
})

export const dropdownOpen = writable(false)
// export const state = writable<WebviewState>(DEFAULT_STATE)
export const loading = writable(false)
export const progressResponse = writable('')