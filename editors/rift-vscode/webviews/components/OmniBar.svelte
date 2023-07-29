<script lang="ts">
  import SendSvg from "./icons/SendSvg.svelte"
  import { dropdownStatus, state } from "./stores"
  import SlashDropdown from "./chat/dropdown/SlashDropdown.svelte"
  import { tick } from "svelte"
  import AtDropdown from "./chat/dropdown/AtDropdown.svelte"
  import type { AtableFile } from "../../src/types"
  import { onMount, onDestroy } from "svelte"
  import { Editor } from "@tiptap/core"
  import StarterKit from "@tiptap/starter-kit"
  import { Placeholder } from "@tiptap/extension-placeholder"
  import type { Transaction } from "@tiptap/pm/state"
  import { FileChip } from "./FileChip"

  let isFocused = true

  let _container: HTMLDivElement | undefined

  let hasInput = false
  state.subscribe((s) => {
    if (s.selectedAgentId) {
      if (s.agents[s.selectedAgentId].inputRequest) {
        hasInput = true
      }
    }
    isFocused = s.isFocused
    if (isFocused) {
      focus()
    }
    hasInput = false
  })

  function sendMessage() {
    console.log("sending message")
    if ($state.agents[$state.selectedAgentId].isStreaming) {
      console.log("cannot send messages while ai is responding")
      return
    }
    blur()

    console.log("chat history")
    console.log($state.agents[$state.selectedAgentId].chatHistory)

    let appendedMessages = $state.agents[$state.selectedAgentId].chatHistory
    appendedMessages?.push({ role: "user", content: editorContent })
    console.log("appendedMessages")
    console.log(appendedMessages)

    if (!$state.agents[$state.selectedAgentId]) throw new Error()

    vscode.postMessage({
      type: "chatMessage",
      agent_id: $state.selectedAgentId,
      agent_type: $state.agents[$state.selectedAgentId].type,
      messages: appendedMessages,
      message: editorContent,
    })

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
    focus()
    // resize()
  }

  function handleValueChange({ editor, transaction }: { editor: Editor; transaction: Transaction }) {
    editorContent = editor.getText()
    console.log('handleValueChange: ',editorContent)

    const shouldShowAtDropdown = () => {
      latestAtToEndOfTextarea = editorContent.lastIndexOf("@") > -1 ? editorContent.slice(editorContent.lastIndexOf("@")) : undefined
      return Boolean(latestAtToEndOfTextarea)
    }
    
    if (editorContent.trim().startsWith("/")) {
      console.log("setting slash")
      dropdownStatus.set("slash")
    } else if (shouldShowAtDropdown()) {
      console.log("setting at")
      dropdownStatus.set("at")
    } else {
      console.log('setting none')
      dropdownStatus.set('none')
    }
  }

  dropdownStatus.subscribe((s) => console.log("dropdownStatus!:", s))

  function handleKeyDown(e: KeyboardEvent) {
    console.log("handleKeydown")

    if (e.key === "Enter") {
      // 13 is the Enter key code
      console.log('preventing default')
      // e.preventDefault() // Prevent default Enter key action

      if (e.shiftKey) return
      if(!editorContent) resetTextarea()
      if (!editorContent || $dropdownStatus == "slash" || $dropdownStatus == 'at') return
      sendMessage()
    }
  }

  function handleRunAgent(agent_type: string) {
    if (!$state.availableAgents.map((x) => x.agent_type).includes(agent_type))
      throw new Error("attempt to run unavailable agent")
    vscode.postMessage({
      type: "runAgent",
      agent_type,
    })

    // textareaValue = ""; //clear omnibar text
    resetTextarea()
    dropdownStatus.set("none")
  }

  let onFocus = async () => {
    isFocused = true
    vscode.postMessage({
      type: "sendHasNotificationChange",
      agentId: $state.selectedAgentId,
      hasNotification: false,
    })
    vscode.postMessage({
      type: "focusOmnibar",
    })
    focus()
    await tick()
  }

  let onBlur = () => {
    isFocused = false
    vscode.postMessage({
      type: "blurOmnibar",
    })
  }

  function handleAddChip(file: AtableFile) {

    console.log("handle add chip:", file.fileName)
    const spanEl = document.createElement("span")

    if (!editor) throw new Error("")
    console.log("editorJSON:")
    console.log(editor.getJSON())


    editor.chain().insertContent(`<span>${file.fileName}</span>`).insertContent(' ').run()
    // editor.commands.selectNodeForward()	


    // console.log('editorJSONafter insert:')
    // console.log(editor.getJSON())
    // editor.view.pasteHTML(HTML)
    // editor.commands.setParagraph()

    // _container.textContent = textareaValue.slice(0, -latestAtToEndOfTextarea.length)

    // _container.appendChild(spanEl)
    // const txtNode = document.createTextNode("\xA0")
    // _container.appendChild(txtNode)

    // const range = document.createRange()
    // const selection = window.getSelection()
    // range.setStart(txtNode, 0)
    // range.setEnd(txtNode, 0)

    // selection?.removeAllRanges()
    // selection?.addRange(range)
  }

  let latestAtToEndOfTextarea: string | undefined = undefined
  $: console.log("latestAtTOEndOfTextarea:", latestAtToEndOfTextarea)

  const focus = () => editor?.view.focus()
  const blur = () => editor?.commands.blur()

  function resetTextarea() {
    editor?.commands.clearContent()
  }

  function disableDefaults(event: Event) {
    const e = event as KeyboardEvent
    const keyCodes = ["ArrowUp", "ArrowDown"]

    if (keyCodes.includes(e.code)) {
      event.preventDefault()
    }

    if(e.code === 'Enter' && $dropdownStatus != 'none') event.preventDefault()
   
  }

  let editor: Editor | undefined
  onMount(() => {
    editor = new Editor({
      element: _container,
      extensions: [
        StarterKit,
        FileChip.configure({
          HTMLAttributes: {
            class: "text-red-400",
          },
        }),
        Placeholder.configure({
          emptyEditorClass: "is-editor-empty",
          placeholder: "Type to chat or hit / for commands",
        }),
      ],
      editorProps: {
        attributes: {
          class: "outline-none focus:outline-none max-h-40",
        },
      },
      content: "",
      onTransaction: (props) => {
        // force re-render so `editor.isActive` works as expected
        editor = editor
      },
      onFocus,
      onBlur,
      onUpdate: handleValueChange,
      onSelectionUpdate: (props) => {
        console.log("onSelection update:", props)
      },
    })

    const editorRootElement = document.querySelector(".ProseMirror")
    if (!editorRootElement) throw new Error()
    editorRootElement.addEventListener("keydown", disableDefaults, true)
  })
  onDestroy(() => {
    const editorRootElement = document.querySelector(".ProseMirror")
    editorRootElement?.removeEventListener("keydown", disableDefaults, true)
    editor?.destroy()
  })

  let editorContent = ""
  $: {editorContent = editor?.getText() ?? ""
}

</script>

<div class="p-2 border-t border-b border-[var(--vscode-input-background)] w-full relative">
  <div
    class={`w-full text-md p-2 bg-[var(--vscode-input-background)] rounded-md flex flex-row items-center border ${
      isFocused ? "border-[var(--vscode-focusBorder)]" : "border-transparent"
    }`}>
    <div
      id="omnibar"
      class="w-full bg-transparent resize-none overflow-visible hide-scrollbar max-h-40"
      bind:this={_container}
      on:keydown={handleKeyDown} />
    <div class="justify-self-end flex">
      <button on:click={sendMessage} class="items-center flex">
        <SendSvg />
      </button>
    </div>
  </div>
  {#if $dropdownStatus == "slash"}
  <SlashDropdown textareaValue={editorContent} {handleRunAgent} />
  {/if}
  
  {#if $dropdownStatus == "at"}
  <AtDropdown {editorContent} {handleAddChip} />
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

  :global(.ProseMirror p.is-editor-empty:first-child::before) {
    color: #adb5bd;
    content: attr(data-placeholder);
    float: left;
    height: 0;
    pointer-events: none;
  }
</style>
