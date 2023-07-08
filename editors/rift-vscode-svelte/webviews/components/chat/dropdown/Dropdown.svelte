<script lang="ts">
  import { state } from "../../stores";
  import DropdownCard from "./DropdownCard.svelte";
  import { onMount } from "svelte";
  const MOCK_AGENT_IDS = [
    "rift-chat",
    "aider",
    "gpt-engineer",
    "auto-code-review",
    "repl-auto-debug",
  ];
  export let agentIds = MOCK_AGENT_IDS;
  onMount(() => {
    // Request agents when the component mounts
    vscode.postMessage({ command: 'getAgents' });

    // Listen for the response
    window.addEventListener('message', event => {
      const message = event.data;
      switch (message.command) {
        case 'agents':
          // Update the agents list when we receive the response
          agentIds = message.data;
          break;
      }
    });
  });

  
  export let inputValue = "";

  let activeId = 0;

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === "Enter") {
      e.preventDefault();
      const newCurrentlySelectedAgentId = agentIds[activeId];
      state.update((state) => ({
        ...state,
        currentlySelectedAgentId: newCurrentlySelectedAgentId,
      }));
    }
    if (e.key == "ArrowDown") {
      e.preventDefault();
      if (activeId == agentIds.length - 1) activeId = 0;
      else activeId++;
    } else if (e.key == "ArrowUp") {
      e.preventDefault();
      if (activeId == 0) activeId = agentIds.length - 1;
      else activeId--;
    } else return;
  }
</script>

<svelte:window on:keydown={handleKeyDown} />
<div
  class="absolute left-0 bg-[var(--vscode-quickInput-background)] w-full z-20 px-2 drop-shadow-xl"
>
  {#each agentIds.filter(id => id.includes(inputValue.substring(1))) as id, index}
    <DropdownCard {id} focused={Boolean(index == activeId)} />
  {/each}
</div>
