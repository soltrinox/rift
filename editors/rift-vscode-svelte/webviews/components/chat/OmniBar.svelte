<script lang="ts">
  import SendSvg from "../icons/SendSvg.svelte";
  import UserSvg from "../icons/UserSvg.svelte";
  import { loading, state, dropdownOpen, _state } from "../stores";
  import Dropdown from "./dropdown/Dropdown.svelte";
  import type { WebviewState } from "../../../src/types";
  import { append } from "svelte/internal";

  let isFocused = true;

  function resize(event: Event) {
    let targetElement = event.target as HTMLElement;
    targetElement.style.height = "auto";
    targetElement.style.height = `${targetElement.scrollHeight}px`;
  }

  let inputValue:string = ''

  let textarea: HTMLTextAreaElement|undefined;

  let hasInput = false;
  state.subscribe((s) => {
    if (s.selectedAgentId) {
      if (s.agents[s.selectedAgentId].inputRequest) {
        hasInput = true;
      }
    }
    hasInput = false;
  });

  function sendMessage() {
    if(!textarea) throw new Error()
    if ($loading) {
      console.log("cannot send messages while ai is responding");
      return;
    }
    textarea.blur();
    loading.set(true);

    console.log("chat history");
    console.log($state.agents[$state.selectedAgentId].chatHistory);

    let appendedMessages = $state.agents[$state.selectedAgentId].chatHistory;
    appendedMessages.push({ role: "user", content: textarea.value });
    console.log("appendedMessages");
    console.log(appendedMessages);

    if(!$state.agents[$state.selectedAgentId]) throw new Error()
    let message = {
      type: "chatMessage",
      agent_id: $state.selectedAgentId,
      agent_type: $state.agents[$state.selectedAgentId].type,
      messages: appendedMessages,
      message: textarea.value,
    };

    console.log("sendMEssage", message);

    vscode.postMessage(message);

    // console.log("updating state...");
    state.update((state: WebviewState) => ({
      ...state,
      agents: {
        ...state.agents,
        [state.selectedAgentId]: {
          ...state.agents[state.selectedAgentId],
          chatHistory: appendedMessages,
        },
      },
    }));
    textarea.value = "";
    textarea.focus();
    textarea.style.height = "auto";
    textarea.style.height = textarea.scrollHeight + "px";
  }

  function handleValueChange(e: Event) {
    if(!textarea) throw new Error()
    inputValue = textarea.value
    resize(e);
    if (textarea.value.trim().startsWith("/")) {
      dropdownOpen.set(true);
    } else dropdownOpen.set(false);
  }

  function handleKeyDown(e: KeyboardEvent) {
    if(!textarea) throw new Error()
    if (e.key === "Enter") {
      // 13 is the Enter key code
      e.preventDefault(); // Prevent default Enter key action
      if (e.shiftKey) {
        textarea.value = textarea.value + "\n";
        textarea.style.height = "auto";
        textarea.style.height = textarea.scrollHeight + "px";
        return;
      }
      if (!textarea.value || $dropdownOpen) return;
      sendMessage();
    }
  }

  function handleRunAgent(agent_type: string) {
    if(!textarea) throw new Error()
    if (!$state.availableAgents.map((x) => x.agent_type).includes(agent_type))
      throw new Error("attempt to run unavailable agent");
    vscode.postMessage({
      type: "runAgent",
      params: {
        agent_type,
        agent_params: {},
      },
    });

    textarea.value = ""; //clear omnibar text
    dropdownOpen.set(false);
  }


  
</script>

<!-- bg-[var(--vscode-panel-background)] -->

<div
  class="p-2 border-t border-b border-[var(--vscode-input-background)] w-full relative"
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
      placeholder={hasInput
        ? $state.agents[$state.selectedAgentId].inputRequest?.place_holder
        : "Type to chat or hit / for commands"}
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
  {#if $dropdownOpen}
  <Dropdown {inputValue} {handleRunAgent} />
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
