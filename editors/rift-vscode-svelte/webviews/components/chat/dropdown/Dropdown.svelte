<script lang="ts">
  import { state } from "../../stores";
  import type { AgentRegistryItem } from "../../../../src/types";
  import DropdownCard from "./DropdownCard.svelte";
  import { onMount } from "svelte";
  import type { SvelteStore } from "../../../../src/types";

  export let handleRunAgent: (agent_type: string) => void;
  let store: SvelteStore;

  state.subscribe((s) => {
    store = s;
  });

  let availableAgents: AgentRegistryItem[] = $state.availableAgents;

  onMount(() => {
    //response is saved to state in ChatWebview.svelte
    vscode.postMessage({ type: "listAgents" });
  });

  console.log("in dropdown: " + JSON.stringify(availableAgents));

  export let inputValue: string = "";

  let activeId = 0;

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === "Enter") {
      e.preventDefault();
      // create agent
      console.log("agent_type: " + availableAgents[activeId].agent_type);
      handleRunAgent(availableAgents[activeId].agent_type);
    }
    if (e.key == "ArrowDown") {
      console.log("ArrowDown");
      console.log(`${store.selectedAgentId}`);
      console.log("THIS IS THE STATE");
      console.log(store);
      e.preventDefault();
      if (activeId == availableAgents.length - 1) activeId = 0;
      else activeId++;
    } else if (e.key == "ArrowUp") {
      console.log("ArrowUp");
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
  {#each availableAgents.filter((agent) => {
    let searchString = inputValue.substring(1).toLowerCase();
    return agent.agent_type
        .toLowerCase()
        .includes(searchString) || agent.display_name
        .toLowerCase()
        .includes(searchString) || agent.agent_description
        .toLowerCase()
        .includes(searchString);
  }) as agent, index}
    <DropdownCard {agent} focused={index === activeId} {handleRunAgent} />
  {/each}
</div>
