<script lang="ts">
  import { onMount } from "svelte"
  import UserSvg from "../icons/UserSvg.svelte"
  import { Editor } from "@tiptap/core"
  import StarterKit from "@tiptap/starter-kit"
  import Placeholder from "@tiptap/extension-placeholder"
  import { FileChip } from "../FileChip"
  
  export let editorContentString: string = "";

  // export let message:string 

  // TODO Pass in message and add parsing function???


  let textarea: HTMLDivElement; //used to be a textarea
  // let editor: Editor | undefined
  
  // let editor: Editor | undefined

  // onMount(() => {


//     editor = new Editor({
//       element: textarea,
//       extensions: [
//         StarterKit,
//         FileChip,
//       ],
//       editable: false,
//       editorProps: {
//         attributes: {
//           class: "outline-none focus:outline-none max-h-40 overflow-auto",
//         },
//       },
//       content: `<span data-type="filechip" data-name="example.ts" data-fullpath="path/to/example.ts"></span>`,
//       onTransaction: (props) => {
//         // force re-render so `editor.isActive` works as expected
//         editor = editor
//       },
//     })
//   })

</script>


<div class="bg-[var(--vscode-input-background)] w-full p-[10px]">
  <div class="flex items-center pb-[6px]">
    <UserSvg classes='mr-2' />
    <p class="text-sm font-semibold">YOU</p>
  </div>
  <div class="text-md flex flex-row items-center">
    <div
      bind:innerHTML={editorContentString}
      contenteditable="false"
      >
    </div>
  </div>
</div>
