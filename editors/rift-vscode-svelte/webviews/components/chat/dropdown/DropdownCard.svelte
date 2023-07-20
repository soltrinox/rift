<script lang="ts">
  import { state } from "../../stores";
  import RiftSvg from "../../icons/RiftSvg.svelte";
  import type { AgentRegistryItem } from "../../../../src/types";

  export let focused: boolean = false;
  export let handleRunAgent: (agent_type: string) => void;
  export let agent: AgentRegistryItem;
</script>

<!-- svelte-ignore a11y-click-events-have-key-events -->
<!-- only disabling this because we already are handling onkeydown-->
<div
  class={`flex flex-col drop-shadow-[5px_-10px_10px_rgba(0,0,0,0.25)] rounded-lg p-2 hover:cursor-pointer ${
    focused
      ? "bg-[var(--vscode-quickInputList-focusBackground)]"
      : "hover:bg-[var(--vscode-list-hoverBackground)]"
  }`}
  on:click={() => handleRunAgent(agent.agent_type)}
>
  <div class="flex flex-row">
    {#if agent.agent_icon}
      {agent.agent_type}
    {:else}
      <RiftSvg />
    {/if}
    /{agent.agent_type}
  </div>
  <!-- <div>
    {agent.display_name}
  </div> -->
  <div class="text-[var(--vscode-gitDecoration-ignoredResourceForeground)]">
    {agent.agent_description}
  </div>
</div>
