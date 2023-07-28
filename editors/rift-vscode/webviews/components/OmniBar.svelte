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

  $: console.log('textareaValue:',textareaValue)

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
    resetTextarea()
    console.log('textareaValue after reset:', textareaValue);
    focus();
    // resize()
  }

  function handleValueChange(e:Event) {
    const target = e.target as HTMLDivElement
    if (!target) throw new Error();
    textareaValue = target.textContent ?? ''
    console.log('handleValueChange called:', textareaValue)
    console.log('latestAtToEndOfTextarea:', latestAtToEndOfTextarea)
    latestAtToEndOfTextarea = textareaValue.lastIndexOf('@') > -1 ? textareaValue.slice(textareaValue.lastIndexOf('@')) : undefined
    if (textareaValue.trim().startsWith("/")) {
      console.log('setting slash')
      dropdownStatus.set('slash')
    } else if (Boolean(latestAtToEndOfTextarea)) {
      console.log('setting at')
      dropdownStatus.set('at')
    } else {
      console.log('setting none')
      dropdownStatus.set('none');}
  }

  dropdownStatus.subscribe(s => console.log('dropdownStatus!:',s))

  function handleKeyDown(e: KeyboardEvent) {
    console.log('handleKeydown')
    if (e.key === "Enter") {
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

    // textareaValue = ""; //clear omnibar text
    resetTextarea()
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
    if(!latestAtToEndOfTextarea) throw new Error()
    console.log('handle add chip:', file.fileName)
    const spanEl = document.createElement('span')
    spanEl.classList.add('text-red-400')
    spanEl.innerText = '@'+file.fileName
    if(!_textarea) throw new Error()
    _textarea.textContent = textareaValue.slice(0, -latestAtToEndOfTextarea.length)
    _textarea.appendChild(spanEl)
  }
  let latestAtToEndOfTextarea:string|undefined = undefined
  $: console.log('latestAtTOEndOfTextarea:', latestAtToEndOfTextarea)

  const focus = () => _textarea?.focus()
  const blur = () => _textarea?.blur()
  const addNewLine = () => {
    if(!_textarea) return
    console.log('addnewline called. old textarea value:', textareaValue)
    // textareaValue = textareaValue + "\n";
    _textarea.textContent = _textarea.textContent + "\n"

    console.log('newtextarea value:', textareaValue)
    // resize()
  }
  // function resize() {
  //   if(!_textarea) return
  //   _textarea.style.height = "auto";
  //   _textarea.style.height = `${_textarea.scrollHeight}px`;
  // }
  function resetTextarea() {
    if(!_textarea) return
    _textarea.textContent = ''
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
      </div>
    <div class="justify-self-end flex">
      <button on:click={sendMessage} class="items-center flex">
        <SendSvg />
      </button>
    </div>
  </div>
  {#if $dropdownStatus == 'slash'}
    <SlashDropdown {textareaValue} {handleRunAgent} />
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
