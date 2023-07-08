<script>
  import RiftSvg from "./icons/RiftSvg.svelte";
  import ResetSvg from "./icons/ResetSvg.svelte";
  import { state, DEFAULT_STATE } from "./stores";
  function resetState() {
    console.log("reseting state");
    state.set(DEFAULT_STATE);
    vscode.setState(DEFAULT_STATE);
  }
</script>

<!-- maybe -->
<div
  class={`top-0 w-full px-2 py-1 flex justify-between z-10  bg-[var(--vscode-input-background)] `}
>
  <div
    class="flex flex-row text-xl items-center text-[var(--vscode-icon-foreground)]"
  >
    <RiftSvg color="var(--vscode-icon-foreground)" />
    {$state.selectedAgentId}
  </div>
  <div class="justify-self-end flex-shrink-0">
    <button class="flex items-center flex-shrink" on:click={resetState}>
      <ResetSvg />
    </button>
  </div>
</div>
