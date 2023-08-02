<script lang="ts">
  import SendSvg from "./icons/SendSvg.svelte"
  import { dropdownStatus, filteredAgents, filteredFiles, focusedFileIndex, state } from "./stores"
  import SlashDropdown from "./chat/dropdown/SlashDropdown.svelte"
  import {onDestroy, onMount, tick} from "svelte"
  import AtDropdown from "./chat/dropdown/AtDropdown.svelte"
  import type {AgentRegistryItem, AtableFile} from "../../src/types"
  import {CommandProps, Editor} from "@tiptap/core"
  import StarterKit from "@tiptap/starter-kit"
  import { Placeholder } from "@tiptap/extension-placeholder"
  import type { Transaction } from "@tiptap/pm/state"
  import type { SuggestionOptions } from "@tiptap/suggestion"
  import { FileChip } from "./FileChip"


const suggestion:Omit<SuggestionOptions<AtableFile>, 'editor'> = {
  items: ({ query }) => {
        const filteredFiles = Array.from(
          new Set([...$state.files.recentlyOpenedFiles, ...$state.files.nonGitIgnoredFiles])
        ).filter((file) => {
        let searchString = query
        return (
          file.fileName.toLowerCase().includes(searchString) ||
          file.fromWorkspacePath.toLowerCase().includes(searchString)
        )
      }).slice(0, 4)
      console.log('new filtered files:', filteredFiles)
      return filteredFiles
  },

  render: () => {
    return {
      onStart: (props) => {
        dropdownStatus.set("at") 
        filteredFiles.set(props.items.map(file => ({...file, onEnter: () => {
          console.log('onEnter called :D')
          props.command(file)}}))) // add the enter command to the files
        },
        
        onUpdate(props) {
          dropdownStatus.set("at") 
          filteredFiles.set(props.items.map(file => ({...file, onEnter: () => {
          console.log('onEnter called :D')
          props.command(file)}})))
      },

      onKeyDown(props) {
        console.log('onKeyDown suggestion plugin: props:', props)
        if (props.event.key === "Escape") {
          // popup[0].hide()
          dropdownStatus.set('none')
          return true // BRENT: I'm guessing return true here means kill the search process.
          // return true
        }
        if(props.event.key == 'ArrowUp') {
          props.event.preventDefault() //necessary to prevent moving the cursor
          focusedFileIndex.update(i => (i + $filteredFiles.length - 1) % $filteredFiles.length)
        }
        
        if(props.event.key == 'ArrowDown') {
          props.event.preventDefault() //necessary to prevent moving the cursor
          focusedFileIndex.update(i => (i + 1) % $filteredFiles.length)
        }

        
        return false
      },

      onExit() {
        dropdownStatus.set('none')
        focusedFileIndex.set(0)
      },
    }
  },
}


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
    if(!editor) throw new Error("no editor in sendMEssage() function in OmniBar.svelte")
    const HTML = editor.getHTML()

    appendedMessages.push({ role: "user", content: editorContent, editorContentString: HTML })
    console.log("appendedMessages")
    console.log(appendedMessages)

    if (!$state.agents[$state.selectedAgentId]) throw new Error()

    vscode.postMessage({
      type: "chatMessage",
      agent_id: $state.selectedAgentId,
      agent_type: $state.agents[$state.selectedAgentId].type,
      messages: appendedMessages,
      message: editorContent,
      editorContentString: HTML,
    })
    console.log("editorContentString for testing:", HTML)

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
    console.log("handleValueChange: ", editorContent)

    // const shouldShowAtDropdown = () => {
    //   latestAtToEndOfTextarea =
    //     editorContent.lastIndexOf("@") > -1 ? editorContent.slice(editorContent.lastIndexOf("@")) : undefined
    //   return Boolean(latestAtToEndOfTextarea)
    // }
    let newFilteredAgents: AgentRegistryItem[] = []
    if (editorContent.trim().startsWith("/")) {
      let searchString = editorContent.substring(1).toLowerCase()
      newFilteredAgents = $state.availableAgents.filter((agent) => {
        return (
          agent.agent_type.toLowerCase().includes(searchString) ||
          agent.display_name.toLowerCase().includes(searchString)
        )
      })
      filteredAgents.set(newFilteredAgents) // im not proud
    } else filteredAgents.set([])

    if (editorContent.trim().startsWith("/") && newFilteredAgents.length > 0) {
      console.log("setting slash")
      dropdownStatus.set("slash")
     } else if($dropdownStatus == 'slash') {
      console.log("setting none")
      dropdownStatus.set("none")
    }
  }

  dropdownStatus.subscribe((s) => console.log("dropdownStatus!:", s))

  function handleKeyDown(e: KeyboardEvent) {
    console.log("handleKeydown")

    if (e.key === "Enter") {
      // 13 is the Enter key code
      // console.log("preventing default")
      // e.preventDefault() // Prevent default Enter key action

      if (e.shiftKey) return
      if (!editorContent) resetTextarea()
      if($dropdownStatus == 'at') {
        $filteredFiles[$focusedFileIndex].onEnter()
        return
      }
      if (!editorContent || $dropdownStatus == "slash") return
      sendMessage()
    }
  }

  function handleRunAgent(agent_type: string) {
    if (!$state.availableAgents.map((x) => x.agent_type).includes(agent_type))
      throw new Error("attempt to run unavailable agent")
    vscode.postMessage({
      type: "createAgent",
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
/* hopefully deprecated --Brent
  function handleAddChip(file: AtableFile) {
    console.log("handle add chip:", file.fileName)
    const spanEl = document.createElement("span")

    if (!editor) throw new Error("")
    console.log("editorJSON:")
    console.log(editor.getJSON())

    editor
      .chain()
      .command((props: CommandProps) => {
        const { editor, tr, commands, state, dispatch } = props

        const docsize = state.doc.content.size - 1 // oboe :()

        if (!latestAtToEndOfTextarea)
          throw new Error("why is this command being run if theres no latestAtToEndOfTextarea")

        tr.delete(docsize - latestAtToEndOfTextarea.length, docsize)

        return true
      })
      .insertContent(`<span data-fsPath="${file.fullPath}" data-name="${file.fileName}"></span>`)
      .insertContent(" ")
      .run()
  }
  */

  // let latestAtToEndOfTextarea: string | undefined = undefined
  // $: console.log("latestAtTOEndOfTextarea:", latestAtToEndOfTextarea)

  const focus = () => editor?.view.focus()
  const blur = () => editor?.commands.blur()

  function resetTextarea() {
    editor?.commands.clearContent()
  }

  function disableDefaults(event: Event) {
    const e = event as KeyboardEvent
    // const keyCodes = ["ArrowUp", "ArrowDown"]

    // if (keyCodes.includes(e.code)) {
    //   event.preventDefault()
    // }

    if (e.code === "Enter" && $dropdownStatus != "none") event.preventDefault()
  }

  let editor: Editor | undefined
  onMount(() => {
    editor = new Editor({
      element: _container,
      extensions: [
        StarterKit,
        FileChip.configure({
          HTMLAttributes: {
            class: "bg-[var(--vscode-editor-background)] text-xs inline-flex items-center h-[1.5rem]",
          },
          suggestion
        }),
        Placeholder.configure({
          emptyEditorClass: "is-editor-empty",
          placeholder: "Type to chat or hit / for commands",
        }),
      ],
      editorProps: {
        attributes: {
          class: "outline-none focus:outline-none max-h-40 overflow-auto",
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
  $: {
    editorContent = editor?.getText() ?? ""
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
    <SlashDropdown {handleRunAgent} />
  {/if}

  {#if $dropdownStatus == "at"}
    <AtDropdown />
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
