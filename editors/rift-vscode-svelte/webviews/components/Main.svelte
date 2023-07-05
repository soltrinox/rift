<!-- Navbar.svelte -->
<script lang="ts">
  import { onMount, onDestroy, tick } from "svelte";
  import CopySvg from "./icons/CopySvg.svelte";
  import EllipsisSvg from "./icons/EllipsisDarkSvg.svelte";
  import UserInput from "./chat/UserInput.svelte";
  import Response from "./chat/Response.svelte";
  import Logs from "./logs/Logs.svelte";
  import { loading, state } from "./stores";
  import type { ChatAgentProgress } from "../../src/types";
  import Header from "./Header.svelte";
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
    // console.log(event);
    progress = event.data.data as ChatAgentProgress;
    progressResponse = progress.response;
    // console.log(progressResponse);
    isDone = progress.done;
    // for sticky window
    if (chatWindow.scrollHeight > height && fixedToBottom) {
      chatWindow.scrollTo(0, chatWindow.scrollHeight);
    }
    height = chatWindow.scrollHeight;
    // for sticky window^
    if (isDone) {
      state.update((state) => ({
        ...state,
        history: [
          ...state.history,
          { role: "assistant", content: progressResponse },
        ],
      }));
    }
  };
  let chatWindow: HTMLDivElement;
  let fixedToBottom: boolean;
  let height: number;
  onMount(async () => {
    await tick();
    chatWindow.scrollTo(0, chatWindow.scrollHeight);
    height = chatWindow.scrollHeight;
    fixedToBottom =
      chatWindow.clientHeight + chatWindow.scrollTop >=
      chatWindow.scrollHeight - 3;
    chatWindow.addEventListener("scroll", function () {
      if (!chatWindow.scrollTop || !chatWindow.scrollHeight) throw new Error();
      console.log("scroll");
      fixedToBottom = Boolean(
        chatWindow.clientHeight + chatWindow.scrollTop >=
          chatWindow.scrollHeight - 20
      );
    });
  });
</script>

<svelte:window on:message={incomingMessage} />

<div>
  <Header />
  <div>
    <div
      bind:this={chatWindow}
      class="flex flex-col overflow-y-auto max-h-[70vh]"
    >
      {#each $state.history as item}
        {#if item.role == "user"}
          <UserInput value={item.content} />
        {:else}
          <Response value={item.content} />
        {/if}
      {/each}
      {#if !isDone}
        <Response value={progressResponse} />
      {/if}
      <UserInput value={""} enabled={true} />
    </div>
    <div class="max-h-[30vh]">
      <section
        id="divider"
        class="border-t-2 pt-1 pb-2 hero container max-w-screen-lg mx-auto flex justify-center"
      >
        <EllipsisSvg />
      </section>
      <Logs chatDone={isDone} />
    </div>
  </div>
</div>
