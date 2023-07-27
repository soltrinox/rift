<script lang="ts">
  import { state } from "../../stores";
  import RiftSvg from "../../icons/RiftSvg.svelte";
  import type { AgentRegistryItem } from "../../../../src/types";
  import FileIconSvg from "../../icons/FileIconSvg.svelte"

  export let focused: boolean = false;
  export let handleHitDropdownCard: (...args: any) => any;
  export let displayName = 'example.ts'
  export let description = '/project/server/example.ts'
</script>

<!-- svelte-ignore a11y-click-events-have-key-events -->
<!-- only disabling this because we already are handling onkeydown-->
<div class="bg-[var(--vscode-editor-background)]">
  <div
    class={`flex flex-col hover:cursor-pointer pl-2 py-2
    ${
      focused
        ? "bg-[var(--vscode-editor-hoverHighlightBackground)]"
        : "bg-[var(--vscode-editor-background)]"
    }`}
    on:click={handleHitDropdownCard}
  >
    <div class="flex flex-row ml-[6px]">
        <FileIconSvg/>
      {displayName}
    </div>
    <div
      class="text-[var(--vscode-gitDecoration-ignoredResourceForeground)] truncate overflow-hidden ml-[2px]"
    >
      {description}
    </div>
  </div>
</div>
