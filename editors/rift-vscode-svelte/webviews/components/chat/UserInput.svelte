<script lang="ts">
  import SendSvg from "../icons/SendSvg.svelte";
  import UserSvg from "../icons/UserSvg.svelte";
  import { loading, state } from "../stores";
  import type { SvelteStore } from "../../../src/types";
  export let value: string = "";

  function resize(event: Event) {
    let targetElement = event.target as HTMLElement;
    targetElement.style.height = "auto";
    targetElement.style.height = `${targetElement.scrollHeight}px`;
  }

  let textarea: HTMLTextAreaElement;

  function sendMessage() {
    console.log('sendMessage called')
    textarea.blur();
    loading.set(true);

    vscode.postMessage({
      type: "chatMessage",
      agent_id: $state.selectedAgentId,
      agent_type: $state.agents[$state.selectedAgentId].type,
      messages: $state.agents[$state.selectedAgentId].chatHistory,
      message: textarea.value,
    });

    console.log("updating state...");
    state.update((state) => ({
      ...state,
      agents: {
        ...state.agents,
        [state.selectedAgentId]: {
          ...state.agents[state.selectedAgentId],
          chatHistory: [
            ...state.agents[state.selectedAgentId].chatHistory,
            { role: "user", content: textarea.value },
          ],
        },
      },
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
      if (!textarea.value) return;
      sendMessage();
    }
    // logic to handle keydown event
  }
</script>


<div class="bg-[var(--vscode-input-background)] w-full p-2">
  <div class="flex items-center py-1">
    <UserSvg size={12} />
    <p class="text-sm">YOU</p>
  </div>
  <div
    class="w-full text-md flex flex-row items-center"
  >
    <textarea
      bind:this={textarea}
      class="w-full block outline-none focus:outline-none bg-transparent resize-none hide-scrollbar"
      placeholder="Type to chat or hit / for commands"
      on:input={resize}
      on:keydown={handleKeyDown}
      disabled={true}
      {value}
      rows={1}
    />
  </div>
</div>


<style>
  .hide-scrollbar::-webkit-scrollbar {
    display: none;
  }

  .hide-scrollbar {
    -ms-overflow-style: none; /* IE and Edge */
    scrollbar-width: none; /* Firefox */
  }
</style>
