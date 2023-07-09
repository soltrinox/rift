<script lang="ts">
  import { state } from '../../stores'
  import * as client from '../../../../src/client'
  import { v4 as uuidv4 } from 'uuid'
  import { Agent, ChatMessage } from '../../../../src/types'
  // import { Log, ChatMessage } from "../../../../src/types";
  import DropdownCard from './DropdownCard.svelte'
  import { onMount } from 'svelte'
  // const MOCK_AGENT_REGISTRY = [
  //   //TODO get from server
  //   { name: 'rift-chat', description: 'ask me anything ab life bro' },
  //   { name: 'aider', description: 'congrats ur now a 10x engineer' },
  //   { name: 'gpt-engineer', description: 'an engineer but gpt' },
  //   { name: 'auto-code-review', description: 'code review but meaner' },
  //   { name: 'repl-auto-debug', description: 'let me debug for u' },
  // ]
  onMount(() => {
    // Request agents when the component mounts
    agents: client.AgentRegistryItem[] = vscode.postMessage({ type: 'getAgents' });
    // TODO
    export let agentIds = agent;
  });
  // export let agentIds = MOCK_AGENT_REGISTRY
  export let inputValue = ''  


  let activeId = 0

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === 'Enter') {
      e.preventDefault()
      const newSelectedAgentId: string = uuidv4() //TODO check for conflicts with existing uuids
      // const newSelectedAgentId =  agentIds[activeId];
      state.update((state) => ({
        ...state,
        selectedAgentId: newSelectedAgentId,
        agents: {
          ...state.agents,
          [newSelectedAgentId]: new Agent(
            newSelectedAgentId,
            agentIds[activeId].name,
            [new ChatMessage('assistant', 'mock message HELLO HOW CAN I HELp')],
            []
          ),
        },
      }))
    }
    if (e.key == 'ArrowDown') {
      e.preventDefault()
      if (activeId == agentIds.length - 1) activeId = 0
      else activeId++
    } else if (e.key == 'ArrowUp') {
      e.preventDefault()
      if (activeId == 0) activeId = agentIds.length - 1
      else activeId--
    } else return
  }
</script>

<svelte:window on:keydown={handleKeyDown} />
<div class="absolute left-0 bg-[var(--vscode-quickInput-background)] w-full z-20 px-2 drop-shadow-xl">
  {#each agentIds.filter((id) => id.name.includes(inputValue.substring(1))) as id, index}
    <DropdownCard id={id.name} focused={Boolean(index == activeId)} />
  {/each}
</div>
