
<script lang="ts">
  import chalk from "chalk"
  import { onDestroy, onMount, tick } from "svelte"
  import type { ChatAgentProgress } from "../../../src/types"
  import { loading, state } from "../stores"
  import UserSvg from "../icons/UserSvg.svelte"
  import UserInput from "./UserInput.svelte"
  import RiftSvg from "../icons/RiftSvg.svelte"
  import Response from './Response.svelte'
  
  let observer: MutationObserver;
  export let progressResponse = "";
  let isDone = false;


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

<div
bind:this={chatWindow}
class="flex flex-col overflow-y-auto max-h-[70vh]"
>
{#each $state.agents[$state.currentlySelectedAgentId].chatHistory as item}
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