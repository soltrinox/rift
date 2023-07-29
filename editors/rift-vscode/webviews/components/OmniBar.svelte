<script lang="ts">
  // This script section of the OmniBar component handles all the logic and state management.
  // It imports necessary components such as SendSvg and Dropdown, and state variables from the stores.
  // It also declares and defines several functions and variables that are used to control the behavior of the OmniBar.

  // Import the SendSvg component.
  import SendSvg from "./icons/SendSvg.svelte";
  // Import the dropdownOpen and state from the stores.
  import { dropdownOpen, state } from "./stores";
  // Import the Dropdown component.
  import Dropdown from "./chat/dropdown/Dropdown.svelte";
  // Import the tick function from svelte.
  import { tick } from "svelte";

  // Declare a variable 'isFocused' to keep track of the focus state of the OmniBar.
  // It is initially set to true, meaning the OmniBar is focused when the component is first rendered.
  let isFocused = true;

  // Define a function 'resize' to dynamically adjust the height of the OmniBar based on its content.
  // It takes an event object as a parameter, from which it extracts the target element (the OmniBar in this case).
  // It first sets the height of the target element to 'auto', then sets it to the scrollHeight of the element,
  // effectively resizing the OmniBar to fit its content.
  function resize(event: Event) {
    let targetElement = event.target as HTMLElement;
    targetElement.style.height = "auto";
    targetElement.style.height = `${targetElement.scrollHeight}px`;
  }

  // Declare a variable for the input value.
  let inputValue: string = "";

  // Declare a variable for the textarea element.
  let textarea: HTMLTextAreaElement | undefined;

  // Declare a variable for whether the OmniBar has input.
  let hasInput = false;
  // Subscribe to the state and update the isFocused and hasInput variables based on the state.
  state.subscribe((s) => {
    if (s.selectedAgentId) {
      if (s.agents[s.selectedAgentId].inputRequest) {
        hasInput = true;
      }
    }
    isFocused = s.isFocused;
    if (isFocused) {
      textarea?.focus();
    }
    hasInput = false;
  });

  // Define a function to send a message.
  function sendMessage() {
    if (!textarea) throw new Error();
    if ($state.agents[$state.selectedAgentId].isStreaming) {
      console.log("cannot send messages while ai is responding");
      return;
    }
    textarea.blur();

    console.log("chat history");
    console.log($state.agents[$state.selectedAgentId].chatHistory);

    let appendedMessages = $state.agents[$state.selectedAgentId].chatHistory;
    appendedMessages?.push({ role: "user", content: textarea.value });
    console.log("appendedMessages");
    console.log(appendedMessages);

    if (!$state.agents[$state.selectedAgentId]) throw new Error();

    vscode.postMessage({
      type: "chatMessage",
      agent_id: $state.selectedAgentId,
      agent_type: $state.agents[$state.selectedAgentId].type,
      messages: appendedMessages,
      message: textarea.value,
    });

    textarea.value = "";
    textarea.focus();
    textarea.style.height = "auto";
    textarea.style.height = textarea.scrollHeight + "px";
  }

  // Define a function to handle value changes.
  let dropdownCancelled = false;

  let isDoubleSlashAllowed = false;

  function handleValueChange(e: Event) {
    if (!textarea) throw new Error();
    inputValue = textarea.value;
    resize(e);
    
    // Check for the case of typing two slashes.
    if (textarea.value.trim() === "//") {
      dropdownOpen.set(false);
      dropdownCancelled = true;
      if (isDoubleSlashAllowed) {
        textarea.value = "//";
        isDoubleSlashAllowed = false;
      } else {
        textarea.value = "/";
        isDoubleSlashAllowed = true;
      }
      return; // Stop execution here if two slashes were entered.
    }

    // Remainder of the function
    if (textarea.value.trim().startsWith("/") && !textarea.value.trim().startsWith("/ ") && !dropdownCancelled) {
      dropdownOpen.set(true);
    } else {
      dropdownOpen.set(false);
      if (textarea.value.trim() === "") {
        dropdownCancelled = false;
      }
    }
  }

  // Define a function to handle key down events.
  function handleKeyDown(e: KeyboardEvent) {
    if (!textarea) throw new Error();
    if (e.key === "Enter") {
      e.preventDefault(); 
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

  // Define a function to handle running an agent.
  function handleRunAgent(agent_type: string) {
    if (!textarea) throw new Error();
    if (!$state.availableAgents.map((x) => x.agent_type).includes(agent_type))
      throw new Error("attempt to run unavailable agent");
    vscode.postMessage({
      type: "runAgent",
      agent_type,
    });

    textarea.value = ""; 
    dropdownOpen.set(false);
  }

  // Define a function to handle focus events.
  let onFocus = async (event: FocusEvent) => {
    if (!textarea) throw new Error();
    isFocused = true;
    vscode.postMessage({
      type: "sendHasNotificationChange",
      agentId: $state.selectedAgentId,
      hasNotification: false,
    });
    vscode.postMessage({
      type: "focusOmnibar",
    });
    textarea.focus();
    await tick();
    textarea.select();
  };

  // Define a function to handle blur events.
  let onBlur = () => {
    isFocused = false;
    vscode.postMessage({
      type: "blurOmnibar",
    });
  };
</script>

<div
  class="p-2 border-t border-b border-[var(--vscode-input-background)] w-full relative"
  >
  <!-- This is the main OmniBar component. It is a container that includes a textarea for user input and a send button.
       The textarea is where the user types their messages or commands, and the send button is used to submit these messages or commands. -->
  <div
    class={`w-full text-md p-2 bg-[var(--vscode-input-background)] rounded-md flex flex-row items-center border ${
    isFocused ? "border-[var(--vscode-focusBorder)]" : "border-transparent"
    }`}
    >
    <!-- This is the textarea for user input. It binds several events such as input, keydown, focus, and blur to handle user interactions.
         It also binds the 'textarea' variable declared in the script section, allowing the script to control its behavior and content. -->
    <textarea
      id="omnibar"
      bind:this={textarea}
      class="w-full outline-none focus:outline-none bg-transparent resize-none overflow-visible hide-scrollbar max-h-40"
      placeholder={hasInput
      ? $state.agents[$state.selectedAgentId].inputRequest?.place_holder
      : "Type to chat or hit / for commands"}
      on:input={handleValueChange}
      on:keydown={handleKeyDown}
      on:focus={onFocus}
      on:blur={onBlur}
      rows={1}
      />
    <!-- This is the send button. It is a graphical element that the user can interact with to submit their messages or commands.
         When clicked, it triggers the 'sendMessage' function defined in the script section, which handles the message sending logic. -->
    <div class="justify-self-end flex">
      <button on:click={sendMessage} class="items-center flex">
        <SendSvg />
      </button>
    </div>
  </div>
  <!-- If the dropdown is open, display the Dropdown component. -->
  {#if $dropdownOpen}
    <Dropdown {inputValue} {handleRunAgent} />
  {/if}
</div>

<style>
  /* This style hides the scrollbar for the textarea. */

  .hide-scrollbar::-webkit-scrollbar {
    display: none;
  }

  .hide-scrollbar {
    -ms-overflow-style: none; /* IE and Edge */
    scrollbar-width: none; /* Firefox */
  }
</style>
