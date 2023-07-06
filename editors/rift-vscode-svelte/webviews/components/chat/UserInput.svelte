<script lang="ts">
  import SendSvg from "../icons/SendSvg.svelte";
  import UserSvg from "../icons/UserSvg.svelte"
  import { loading, state } from "../stores";
  export let value: string = "";
  export let enabled: boolean = false;

  function resize(event: Event) {
    let targetElement = event.target as HTMLElement;
    targetElement.style.height = "auto";
    targetElement.style.height = `${targetElement.scrollHeight}px`;
  }

  let textarea: HTMLTextAreaElement;

  function sendMessage() {
    textarea.blur();
    loading.set(true);

    vscode.postMessage({
      type: "chatMessage",
      messages: $state.agents[$state.currentlySelectedAgentId].chatHistory,
      message: textarea.value,
    });
    console.log("updating state...");
    state.update((state) => ({
      ...state,
      agents: {
        ...state.agents,
        [state.currentlySelectedAgentId]: {
          ...state.agents[state.currentlySelectedAgentId],
          chatHistory: [ 
            ...state.agents[state.currentlySelectedAgentId].chatHistory, {role: "user", content: textarea.value}
          ]
        }
      }
    }));
    textarea.value = "";
    textarea.focus();
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === "Enter") {
      // 13 is the Enter key code
      e.preventDefault(); // Prevent default Enter key action
      if (e.shiftKey) {
        textarea.value = textarea.value + "\n";
        textarea.style.height = "auto";
        textarea.style.height = textarea.scrollHeight + "px";
        return;
      }
      if (!textarea.value) return
      sendMessage();
    }
    // logic to handle keydown event
  }
</script>


<div
class="flex items-center pt-2 pl-2 bg-[var(--vscode-input-background)]"
>
<UserSvg size={12} />
<p class="text-sm">YOU</p>
</div>
<div
  class="w-full text-md p-2 min-h-8 bg-[var(--vscode-input-background)] flex flex-row items-center"
>
  <textarea
    bind:this={textarea}
    class="w-full min-h-8 block outline-none focus:outline-none bg-transparent resize-none"
    placeholder="Type to chat or hit / for commands"
    on:input={resize}
    on:keydown={handleKeyDown}
    disabled={!enabled}
    {value}
  />
  {#if enabled}
    <div class="justify-self-end flex">
      <button on:click={sendMessage} class="items-center flex">
        <SendSvg />
      </button>
    </div>
  {/if}
</div>
