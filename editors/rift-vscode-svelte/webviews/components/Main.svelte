<!-- Navbar.svelte -->
<script lang="ts">
  import { onMount, onDestroy, tick } from "svelte";
  import CopySvg from "./icons/CopySvg.svelte";
  import EllipsisSvg from "./icons/EllipsisDarkSvg.svelte";
  import UserSvg from "./icons/UserSvg.svelte";
  import RiftSvg from "./icons/RiftSvg.svelte";
  import UserInput from "./chat/UserInput.svelte";
  import Response from "./chat/Response.svelte";
  import Logs from "./logs/Logs.svelte";
  import { loading, state } from "./stores";
  import type { ChatAgentProgress } from "../../src/types";
  import Header from "./Header.svelte";
  import chalk from "chalk";
  state.subscribe((state) => {
    // state.history.splice(0);

    if (!state.history.length) return; // don't want initial rendering to fuck this up
    vscode.setState(state);
  });

  let progress: ChatAgentProgress;
  let observer: MutationObserver;
  let progressResponse = "";
  let isDone = false;
  const vscodeState = vscode.getState();
  console.log("attempting to access vscode state:");
  console.log(vscodeState);
  if (vscodeState && vscodeState.history.length) state.set(vscodeState);

  const incomingMessage = (event: any) => {
    // console.log(event);
    progress = event.data.data as ChatAgentProgress;
    progressResponse = progress.response;
    // console.log(progressResponse);
    isDone = progress.done;
    // for sticky window
    // if (chatWindow.scrollHeight > height && fixedToBottom) {
    //   chatWindow.scrollTo(0, chatWindow.scrollHeight);
    // }
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
      loading.set(false);
    }
  };
  let chatWindow: HTMLDivElement;
  $: {
    console.log("change");
    chatWindow?.scrollTo(0, chatWindow.scrollHeight);
  }
  let fixedToBottom: boolean;
  let height: number;
  function scrollToBottomIfNearBottom() {
    console.log("scrolling?:");
    // fixedToBottom = Boolean(
    //     chatWindow.clientHeight + chatWindow.scrollTop >=
    //       chatWindow.scrollHeight - 30
    //   );
    if (fixedToBottom) console.log("scrolling");
    else console.log("not scrolling");
    if (fixedToBottom) chatWindow.scrollTo(0, chatWindow.scrollHeight);
  }
  onMount(async () => {
    console.log("awaiting tick");
    await tick();
    chatWindow.scrollTo(0, chatWindow.scrollHeight);

    observer = new MutationObserver(scrollToBottomIfNearBottom);
    observer.observe(chatWindow, { childList: true, subtree: true });

    fixedToBottom = Boolean(
      chatWindow.clientHeight + chatWindow.scrollTop >=
        chatWindow.scrollHeight - 15
    );
    // height = chatWindow.scrollHeight;
    chatWindow.addEventListener("scroll", function () {
      if (!chatWindow.scrollTop || !chatWindow.scrollHeight) {
        console.log(chatWindow);
        console.log(chatWindow.scrollTop);
        console.log(chatWindow.scrollHeight);
        throw new Error();
      }
      console.log(chalk.blue("scroll"));
      fixedToBottom = Boolean(
        chatWindow.clientHeight + chatWindow.scrollTop >=
          chatWindow.scrollHeight - 15
      );
    });
  });
  onDestroy(() => {
    observer.disconnect();
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
          <div
            class="flex items-center pt-2 pl-2 bg-[var(--vscode-input-background)]"
          >
            <UserSvg size={12} />
            <p class="text-sm">YOU</p>
          </div>
          <UserInput value={item.content} />
        {:else}
          <div class="flex items-center pt-2 pl-2">
            <RiftSvg size={12} />
            <p class="text-sm">RIFT</p>
          </div>
          <Response value={item.content} />
        {/if}
      {/each}
      {#if !isDone}
        <div
          class="flex items-center pt-2 pl-2 bg-[var(--vscode-input-background)]"
        >
          <RiftSvg size={12} />
          <p class="text-sm">RIFT</p>
        </div>
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
