<script lang="ts">
  import SendSvg from "../icons/SendSvg.svelte";
  import UserSvg from "../icons/UserSvg.svelte";
  import { loading, state } from "../stores";
  import Dropdown from "./dropdown/Dropdown.svelte";
  import type { SvelteStore } from "../../../src/types";
  let dropdownOpen = false;
  let isFocused = true;
  let currentSlashCommand = "";

  function resize(event: Event) {
    let targetElement = event.target as HTMLElement;
    targetElement.style.height = "auto";
    targetElement.style.height = `${targetElement.scrollHeight}px`;
  }

  let textarea: HTMLTextAreaElement;

  function sendMessage() {
    textarea.blur();
    loading.set(true);

    let message = {
      type: "chatMessage",
      agent_id: $state.selectedAgentId,
      agent_type: $state.agents[$state.selectedAgentId].type,
      messages: $state.agents[$state.selectedAgentId].chatHistory,
      message: textarea.value,
    };
    console.log("sendMEssage", message);

    vscode.postMessage(message);

    console.log("updating state...");
    state.update((state: SvelteStore) => ({
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
  function handleValueChange(e: Event) {
    resize(e);
    if (textarea.value.trim().startsWith("/")) {
      dropdownOpen = true;
      currentSlashCommand = textarea.value;
    } else dropdownOpen = false;
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
      if (!textarea.value || dropdownOpen) return;
      sendMessage();
    }
  }
</script>

<div
  class="p-2 border-t border-b border-[var(--vscode-input-background)] relative"
>
  <div
    class={`w-full text-md p-2 bg-[var(--vscode-input-background)] rounded-md flex flex-row items-center border ${
      isFocused ? "border-[var(--vscode-focusBorder)]" : "border-transparent"
    }`}
  >
    <textarea
      id="omnibar"
      bind:this={textarea}
      class="w-full outline-none focus:outline-none bg-transparent resize-none overflow-visible hide-scrollbar max-h-40"
      placeholder="Type to chat or hit / for commands"
      on:input={handleValueChange}
      on:keydown={handleKeyDown}
      on:focus={() => {
        isFocused = true;
      }}
      on:blur={() => (isFocused = false)}
      rows={1}
    />
    <div class="justify-self-end flex">
      <button on:click={sendMessage} class="items-center flex">
        <SendSvg />
      </button>
    </div>
  </div>
  {#if dropdownOpen}
    <Dropdown inputValue={currentSlashCommand} />
  {/if}
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
