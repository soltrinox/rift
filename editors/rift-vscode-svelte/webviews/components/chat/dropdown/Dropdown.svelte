<script lang="ts">
  import { state } from "../../stores";
  import type { AgentRegistryItem } from "../../../../src/types";
  import DropdownCard from "./DropdownCard.svelte";
  import { onMount } from "svelte";
  import type { WebviewState } from "../../../../src/types";

  export let handleRunAgent: (agent_type: string) => void;




  let availableAgents: AgentRegistryItem[] = $state.availableAgents;

  let filteredAgents = availableAgents
  let activeId = availableAgents.length-1;

  $: {
    filteredAgents = availableAgents.filter((agent) => {
    let searchString = inputValue.substring(1).toLowerCase();
    return agent.agent_type
        .toLowerCase()
        .includes(searchString) || agent.display_name
        .toLowerCase()
        .includes(searchString)
          || agent.agent_description
        .toLowerCase()
        .includes(searchString);
    })
    activeId = filteredAgents.length-1
    }

  onMount(() => {
    //response is saved to state in ChatWebview.svelte
    vscode.postMessage({ type: "listAgents" });
  });

  console.log("in dropdown: ",availableAgents)

  export let inputValue: string = "";
  if(availableAgents.length < 1) throw new Error('no available agents')

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === "Enter") {
      e.preventDefault();
      // create agent
      console.log("agent_type: " + availableAgents[activeId].agent_type);
      handleRunAgent(availableAgents[activeId].agent_type);
    }
    if (e.key == "ArrowDown") {
      e.preventDefault();
      if (activeId == availableAgents.length - 1) activeId = 0;
      else activeId++;
    } else if (e.key == "ArrowUp") {
      e.preventDefault();
      if (activeId == 0) activeId = availableAgents.length - 1;
      else activeId--;
    } else return;
  }
</script>

<svelte:window on:keydown={handleKeyDown} />

<div
  class="absolute bottom-full left-0 px-2 w-full z-20 drop-shadow-[0_-4px_16px_0px_rgba(0,0,0,0.36)]"
>
  {#each filteredAgents as agent, index}
    <DropdownCard {agent} focused={index === activeId} {handleRunAgent} />
  {/each}
</div>
