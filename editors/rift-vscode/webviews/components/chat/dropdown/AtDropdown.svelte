<script lang="ts">
  import { state, filteredFiles, focusedFileIndex } from "../../stores"
  import type { AtableFile } from "../../../../src/types"
  import AtDropdownCard from "./AtDropdownCard.svelte"

  // this will be the latest @ to the end of the textbox, not including already made chips. if no matches show up then the user will be able to keep typing and the dropdown won't appear.
  
  

  

  // todo: make sure this is working on the individual card level.
  // function handleKeyDown(e: KeyboardEvent) {
  //   console.log("handleKeyDown in AtDropdown, ",$filteredFiles[$focusedFileIndex])
  //   if (e.key === "Enter") {
  //     e.preventDefault()
  //     $filteredFiles[$focusedFileIndex].onEnter()
  //   }
  // }


</script>

<!-- <svelte:window on:keydown={handleKeyDown} /> -->

  <div class="absolute bottom-full left-0 px-2 w-full z-20 drop-shadow-[0_-4px_16px_0px_rgba(0,0,0,0.36)]">
    {#each $filteredFiles as file, index}
      <AtDropdownCard
        focused={index === $focusedFileIndex}
        displayName={file.fileName}
        description={file.fromWorkspacePath}
        onClick={file.onEnter} />
    {/each}
  </div>