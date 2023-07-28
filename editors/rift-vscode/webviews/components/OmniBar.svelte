<script lang="ts">
  import SendSvg from "./icons/SendSvg.svelte";
  import { dropdownStatus, state } from "./stores";
  import SlashDropdown from "./chat/dropdown/SlashDropdown.svelte";
  import { tick } from "svelte";
  import AtDropdown from "./chat/dropdown/AtDropdown.svelte"
  import type { AtableFile } from "../../src/types"

  let isFocused = true;




  let _textarea:HTMLDivElement|undefined
  let inputValue: string = "";
  let textareaValue:string = ''

  let hasInput = false;
  state.subscribe((s) => {
    if (s.selectedAgentId) {
      if (s.agents[s.selectedAgentId].inputRequest) {
        hasInput = true;
      }
    }
    isFocused = s.isFocused;
    if (isFocused) {
      focus();
    }
    hasInput = false;
  });

  function sendMessage() {
    console.log('sending message')
    if ($state.agents[$state.selectedAgentId].isStreaming) {
      console.log("cannot send messages while ai is responding");
      return;
    }
    blur();

    console.log("chat history");
    console.log($state.agents[$state.selectedAgentId].chatHistory);

    let appendedMessages = $state.agents[$state.selectedAgentId].chatHistory;
    appendedMessages?.push({ role: "user", content: textareaValue });
    console.log("appendedMessages");
    console.log(appendedMessages);

    if (!$state.agents[$state.selectedAgentId]) throw new Error();

    vscode.postMessage({
      type: "chatMessage",
      agent_id: $state.selectedAgentId,
      agent_type: $state.agents[$state.selectedAgentId].type,
      messages: appendedMessages,
      message: textareaValue,
    });

    // clint.
    // console.log("updating state...");

    // state.update((state: WebviewState) => ({
    //   ...state,
    //   agents: {
    //     ...state.agents,
    //     [state.selectedAgentId]: {
    //       ...state.agents[state.selectedAgentId],
    //       chatHistory: appendedMessages,
    //     },
    //   },
    // }));
    textareaValue = "";
    console.log('textareaValue after reset:', textareaValue);
    focus();
    resize()
  }

  function handleValueChange(e:Event) {
    const target = e.target as HTMLDivElement
    if (!target) throw new Error();
    textareaValue = target.textContent ?? ''
    console.log('calling replace all on ')

    // textareaValue = target.value.replaceAll('red', '<span style="color: red;">red</span>');
    resize();
    if (textareaValue.trim().startsWith("/")) {
      dropdownStatus.set('slash')
    } else dropdownStatus.set('none');
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === "Enter") {
      console.log('handleKeydown')
      // 13 is the Enter key code
      e.preventDefault(); // Prevent default Enter key action
      if (e.shiftKey) {
        addNewLine()
        return;
      }
      if (!textareaValue || $dropdownStatus !== 'none') return;
      sendMessage();
    }
  }

  function handleRunAgent(agent_type: string) {
    if (!$state.availableAgents.map((x) => x.agent_type).includes(agent_type))
      throw new Error("attempt to run unavailable agent");
    vscode.postMessage({
      type: "runAgent",
      agent_type,
    });

    textareaValue = ""; //clear omnibar text
    dropdownStatus.set('none');
  }

  let onFocus = async (event: FocusEvent) => {
    if (!_textarea) throw new Error();
    isFocused = true;
    vscode.postMessage({
      type: "sendHasNotificationChange",
      agentId: $state.selectedAgentId,
      hasNotification: false,
    });
    vscode.postMessage({
      type: "focusOmnibar",
    });
    focus();
    await tick();
  };

  let onBlur = () => {
    isFocused = false;
    vscode.postMessage({
      type: "blurOmnibar",
    });
  };

  function handleAddChip(file: AtableFile) {

  }
  let latestAtToEndOfTextarea = textareaValue.slice(textareaValue.lastIndexOf('@'))


  const focus = () => _textarea?.focus()
  const blur = () => _textarea?.blur()
  const addNewLine = () => {
    console.log('addnewline called. old text are avalue')
    console.log(textareaValue)
    textareaValue = textareaValue + "\n";

    console.log('new textareavlua:', textareaValue)
    resize()
  }
  function resize() {
    if(!_textarea) return
    _textarea.style.height = "auto";
    _textarea.style.height = `${_textarea.scrollHeight}px`;
  }
</script>


<div
  class="p-2 border-t border-b border-[var(--vscode-input-background)] w-full relative"
>
  <div
    class={`w-full text-md p-2 bg-[var(--vscode-input-background)] rounded-md flex flex-row items-center border ${
      isFocused ? "border-[var(--vscode-focusBorder)]" : "border-transparent"
    }`}
  >
    <div
      id="omnibar"
      class="w-full outline-none focus:outline-none bg-transparent resize-none overflow-visible hide-scrollbar max-h-40"
      placeholder={hasInput
        ? $state.agents[$state.selectedAgentId].inputRequest?.place_holder
        : "Type to chat or hit / for commands"}
      bind:this={_textarea}
      contenteditable="true"
      on:input={handleValueChange}
      on:keydown={handleKeyDown}
      on:focus={onFocus}
      on:blur={onBlur}
    >
    {textareaValue}
      </div>
    <div class="justify-self-end flex">
      <button on:click={sendMessage} class="items-center flex">
        <SendSvg />
      </button>
    </div>
  </div>
  {#if $dropdownStatus == 'slash'}
    <SlashDropdown {inputValue} {handleRunAgent} />
  {:else if  $dropdownStatus == 'at'}
    <AtDropdown {latestAtToEndOfTextarea} {handleAddChip} />
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
