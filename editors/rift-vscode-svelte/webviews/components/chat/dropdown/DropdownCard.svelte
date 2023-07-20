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
  class={`flex flex-col hover:cursor-pointer px-2 py-2
    ${
      focused
        ? "bg-[var(--vscode-editor-hoverHighlightBackground)]"
        : "bg-[var(--vscode-quickInput-background)]"
    }`}
  on:click={() => handleRunAgent(agent.agent_type)}
>
  <div class="flex flex-row">
    {#if agent.agent_icon}
      {agent.agent_type}
    {:else}
      <div class="flex items-center justify-center">
        <RiftSvg size="16" />
      </div>
    {/if}
    <!-- {agent.agent_type} -->
    {agent.display_name}
  </div>
  <!-- <div>
    {agent.display_name}
  </div> -->
  <div
    class="text-[var(--vscode-gitDecoration-ignoredResourceForeground)] truncate overflow-hidden"
  >
    {agent.agent_description}
  </div>
</div>
