<!-- Navbar.svelte -->
<script lang='ts'>
  import { onMount } from 'svelte';
  import CopySvg from './icons/CopySvg.svelte'
  import UserInput from './chat/UserInput.svelte';
  import Response from './chat/Response.svelte'
  import Logs from './logs/Logs.svelte'
  import {loading, state} from './stores'
  import type { ChatAgentProgress } from '../../src/types'
  
  state.subscribe(state => {
    if(!state.history.length) return // don't want initial rendering to fuck this up
    vscode.setState(state)
  })
  
  const vscodeState = vscode.getState()
  console.log('attempting to access vscode state:')
  console.log(vscodeState)
  if(vscodeState && vscodeState.history.length) state.set(vscodeState)
  
    window.addEventListener("message", (event) => {
    if (event.data.type === 'progress') {
      //do stuff
      // l l
      let progress = event.data.data as ChatAgentProgress
      console.log(progress.log)
    }
      
    });

</script>

<div>
  <div style="height: 70vh;" class="flex flex-col">
    {#each $state.history as item}
      {#if item.role == "user"}
        <UserInput value={item.content} />
      {:else}
        <Response value={item.content} />
      {/if}
    {/each}
    <UserInput />
    <Response isNew={true} />
  </div>
  <div style="height: 30vh;">
    <!-- LOGS HERE -->
    <Logs />
  </div>
</div>
