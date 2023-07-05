<script>
  import RiftSvg from './icons/RiftSvg.svelte'
  import ResetSvg from './icons/ResetSvg.svelte'
  import { state, DEFAULT_STATE } from './stores'
  function resetState() {
    state.set(DEFAULT_STATE)
    vscode.setState(DEFAULT_STATE)
  }
</script>

<div class={` top-0 w-full p-2 flex justify-between bg-[var(--vscode-panel-background)] z-10`}>
  <div class="flex flex-row text-xl items-center text-[var(--vscode-icon-foreground)]">
    <RiftSvg color="var(--vscode-icon-foreground)" />
    Rift
  </div>
  <div class="justify-self-end flex-shrink-0">
    <button class="flex items-center flex-shrink" on:click={resetState}>
      <ResetSvg />
    </button>
  </div>
</div>
