<script lang="ts">
  import { onMount } from "svelte"
  import UserSvg from "../icons/UserSvg.svelte"
  import { Editor } from "@tiptap/core"
  import StarterKit from "@tiptap/starter-kit"
  import Placeholder from "@tiptap/extension-placeholder"
  import { FileChip } from "../FileChip"
  

  export let value:string 

  // TODO Pass in message and add parsing function???


  let textarea: HTMLDivElement; //used to be a textarea
  let editor: Editor | undefined
  

/// "random text here [uri](path/to/example.ts) something else here"
// returns "random text here <span type="filechip" data-fullpath="path/to/example.ts" data-filename="example.ts"></span> something else here"
  function parseProseMirrorHTMLfromMessageContent(message:string) {
    const regex = /\[(.*?)\]\((.*?)\)/g;
    return message.replace(regex, '<span type="filechip" data-fullpath="$2" data-filename="$1"></span>');
  }
  
  const editorContent = parseProseMirrorHTMLfromMessageContent(value)
  console.log('editorContent: ', editorContent)

  onMount(() => {


    editor = new Editor({
      element: textarea,
      extensions: [
        StarterKit,
        FileChip,
      ],
      editable: false,
      editorProps: {
        attributes: {
          class: "outline-none focus:outline-none max-h-40 overflow-auto",
        },
      },
      // content: `<span data-type="filechip" data-name="example.ts" data-fullpath="path/to/example.ts"></span>`,
      content: editorContent,
      onTransaction: (props) => {
        // force re-render so `editor.isActive` works as expected
        editor = editor
      },
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
      contenteditable="false"
      >
    </div>
  </div>
</div>
