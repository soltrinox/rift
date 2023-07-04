<!-- Navbar.svelte -->
<script lang="ts">
  import { onMount } from "svelte";
  import CopySvg from "./icons/CopySvg.svelte";
  import UserInput from "./chat/UserInput.svelte";
  import Response from "./chat/Response.svelte";
  import Logs from "./logs/Logs.svelte";
  import { loading, state } from "./stores";
  import type { ChatAgentProgress } from "../../src/types";

  state.subscribe((state) => {
    // state.history.splice(0);

    if (!state.history.length) return; // don't want initial rendering to fuck this up
    vscode.setState(state);
  });

  let progress: ChatAgentProgress;
  let progressResponse = "";
  let isDone = false;
  const vscodeState = vscode.getState();
  console.log("attempting to access vscode state:");
  console.log(vscodeState);
  if (vscodeState && vscodeState.history.length) state.set(vscodeState);

  const incomingMessage = (event) => {
    console.log(event);
    progress = event.data.data as ChatAgentProgress;
    progressResponse = progress.response;
    console.log(progressResponse);
    isDone = progress.done;
    if (isDone) {
    state.update((state) => ({
      ...state, history: [...state.history, { role: "assistant", content: progressResponse }]
    }));
    }
  };

  
</script>

<svelte:window on:message={incomingMessage} />

<div>
  <div style="height: 70vh;" class="flex flex-col overflow-y-auto">
    {#each $state.history as item}
      {#if item.role == "user"}
        <UserInput value={item.content}/>
      {:else}
        <Response value={item.content} />
      {/if}
    {/each}
    {#if !isDone}
      <Response value={progressResponse} />
    {/if}
    <UserInput value={""} enabled={true} />
  </div>
  <div style="height: 30vh;">
    <!-- LOGS HERE -->
    <Logs chatDone={isDone} />
  </div>
</div>
