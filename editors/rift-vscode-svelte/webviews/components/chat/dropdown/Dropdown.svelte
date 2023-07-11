<script lang="ts">
  import {state} from "../../stores";
  import type {AgentRegistryItem} from "../../../../src/types";
  // import { Log, ChatMessage } from "../../../../src/types";
  import DropdownCard from "./DropdownCard.svelte";
  import {onMount} from "svelte";
  // const MOCK_AGENT_REGISTRY = [
  //   //TODO get from server
  //   { name: 'rift-chat', description: 'ask me anything ab life bro' },
  //   { name: 'aider', description: 'congrats ur now a 10x engineer' },
  //   { name: 'gpt-engineer', description: 'an engineer but gpt' },
  //   { name: 'auto-code-review', description: 'code review but meaner' },
  //   { name: 'repl-auto-debug', description: 'let me debug for u' },
  // ]

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

      console.log("THIS IS THE STATE");
      console.log($state);

      vscode.postMessage({
        type: "runAgent",
        params: {
          agent_type: availableAgents[activeId].agent_type,
          agent_params: {},
        },
      });
    }
    if (e.key == "ArrowDown") {
      console.log("ArrowDown");
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

<svelte:window on:keydown={handleKeyDown}/>
<div
        class="absolute bottom-full left-0 bg-[var(--vscode-quickInput-background)] w-full z-20 px-2 drop-shadow-xl"
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
    <DropdownCard {agent} focused={index === activeId}/>
  {/each}
</div>
