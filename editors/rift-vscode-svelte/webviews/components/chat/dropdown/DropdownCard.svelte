<script lang="ts">
  import { state } from "../../stores";
  import RiftSvg from "../../icons/RiftSvg.svelte";
  import type { AgentRegistryItem } from "../../../../src/types";

  export let focused: boolean = false;

  export let agent: AgentRegistryItem;
</script>

<div
  class={`flex flex-col hover:cursor-pointer ${
    focused
      ? "bg-[var(--vscode-quickInputList-focusBackground)]"
      : "hover:bg-[var(--vscode-list-hoverBackground)]"
  }`}
>
  <div class="flex flex-row">
    {#if agent.agent_icon}
      {agent.agent_type}
    {:else}
      <RiftSvg />
    {/if}
    /{agent.agent_type}
  </div>
  <div>
    {agent.display_name}
  </div>
  <div class="text-[var(--vscode-gitDecoration-ignoredResourceForeground)]">
    {agent.agent_description}
  </div>
</div>
