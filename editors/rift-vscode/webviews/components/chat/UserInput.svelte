<script lang="ts">
  import { onMount } from "svelte"
  import UserSvg from "../icons/UserSvg.svelte"
  import { Editor } from "@tiptap/core"
  import StarterKit from "@tiptap/starter-kit"
  import Placeholder from "@tiptap/extension-placeholder"
  import { FileChip } from "../FileChip"
  
  export let editorContentString: string = "";
  let textarea: HTMLDivElement; //used to be a textarea
  // let editor: Editor | undefined
  
  
  // onMount(() => {
  // textarea.innerHTML = editorContentString
  // })

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
