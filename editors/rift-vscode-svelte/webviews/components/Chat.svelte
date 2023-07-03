<!-- Navbar.svelte -->
<script>
  import { onMount } from 'svelte';
  import CopySvg from './icons/CopySvg.svelte'
  import UserInput from './chat/UserInput.svelte';
  import Response from './chat/Response.svelte'
  const vscode = tsvscode
  
  const DEFAULT_STATE = {
    history: [],
  };
  let state = vscode.getState();
  if (!state) {
    vscode.setState(DEFAULT_STATE);
  }

</script>

<div class="flex flex-col">
  {#each vscode.getState().history as item}
    {#if item.role == "user"}
       <UserInput value={item.content} />
    {:else}
        <Response value={item.content} />
    {/if}
  {/each}
  <UserInput />
  <Response />
</div>