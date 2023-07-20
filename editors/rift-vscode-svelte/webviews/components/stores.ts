import { readable, writable } from 'svelte/store'
// import { DEFAULT_STATE } from '../../src/client'
import type { WebviewState } from '../../src/types'


const DEFAULT_STATE: WebviewState = {
  selectedAgentId: '',
  agents: {
  },
  availableAgents: [{
    agent_type: "rift_chat",
    agent_description: '',
    agent_icon: '',
    display_name: 'Rift Chat'
  }],
  isStreaming: false,
  streamingText: ''
}

export const state = readable<WebviewState>(DEFAULT_STATE, (set) => {
  window.addEventListener('message', (event:any) => {
    if(event.data.type != 'stateUpdate') throw new Error('Message passed to webview that is not stateUpdate')
    const newState = event.data.data as WebviewState
    set(newState)
  })
})

export const dropdownOpen = writable(false)
// export const state = writable<WebviewState>(DEFAULT_STATE)
// export const progressResponse = writable('')