<!-- Navbar.svelte -->
<script lang="ts">
  import { onMount } from "svelte";
  import CopySvg from "./icons/CopySvg.svelte";
  import UserInput from "./chat/UserInput.svelte";
  import Response from "./chat/Response.svelte";
  import Logs from "./logs/Logs.svelte";
  import { loading, state } from "./stores";
  state.subscribe((state) => {
    vscode.setState(state);
  });
  const vscodeState = vscode.getState();
  if (vscodeState) state.set(vscodeState);
</script>

<div>
  <div class="flex flex-col">
    <!-- svelte-ignore missing-declaration -->
    {#each vscode.getState().history as item}
      {#if item.role == "user"}
        <UserInput value={item.content} />
      {:else}
        <Response value={item.content} />
      {/if}
    {/each}
    <UserInput />
    <Response isNew={true} />
  </div>
  <div>
    <!-- LOGS HERE -->
    <Logs />
  </div>
</div>
