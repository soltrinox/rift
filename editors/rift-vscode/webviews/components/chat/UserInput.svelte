<script lang="ts">
  import { onMount } from "svelte"
  import UserSvg from "../icons/UserSvg.svelte"
  import { Editor } from "@tiptap/core"
  import StarterKit from "@tiptap/starter-kit"
  import { FileChip } from "../FileChip"
  import Placeholder from "@tiptap/extension-placeholder"
  
  export let editorContentString: string = "";
  let textarea: HTMLDivElement; //used to be a textarea
  let editor: Editor | undefined
  onMount(() => {
    editor = new Editor({
      element: textarea,
      extensions: [
        StarterKit,
        FileChip.configure({
          HTMLAttributes: {
            class: "bg-[var(--vscode-editor-background)] text-xs inline-flex items-center h-[1.5rem]",
            contenteditable: "false",
          },
        })
      ],
      editorProps: {
        attributes: {
          class: "outline-none focus:outline-none max-h-40 overflow-auto",
        },
      },
      content: editorContentString,
      onTransaction: (props) => {
        // force re-render so `editor.isActive` works as expected
        editor = editor
      },
      editable: false,
    })

  })

</script>


<div class="bg-[var(--vscode-input-background)] w-full p-[10px]">
  <div class="flex items-center pb-[6px]">
    <UserSvg classes='mr-2' />
    <p class="text-sm font-semibold">YOU</p>
  </div>
  <div class="text-md flex flex-row items-center">
    <div
      bind:this={textarea}
      >
    </div>
  </div>
</div>
