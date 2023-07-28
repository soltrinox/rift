<script lang="ts">
  import { state } from "../../stores";
  import type { AtableFile } from "../../../../src/types";
  import AtDropdownCard from "./AtDropdownCard.svelte";

  state.subscribe(s => console.log('rOFiles',s.files.recentlyOpenedFiles))

  // this will be the latest @ to the end of the textbox, not including already made chips. if no matches show up then the user will be able to keep typing and the dropdown won't appear.
  export let latestAtToEndOfTextarea: string = ""; 
  export let handleAddChip:(file: AtableFile) => void;

  let atableFiles = Array.from(new Set([...$state.files.recentlyOpenedFiles, ...$state.files.nonGitIgnoredFiles]))

  let filteredFiles = atableFiles;
  let activeId = atableFiles.length - 1;


  $: console.log(filteredFiles)
  
  $: {



    filteredFiles = atableFiles.filter(file => {
      let searchString = latestAtToEndOfTextarea.substring(1).toLowerCase()
      return (
        file.fileName.toLowerCase().includes(searchString) ||
        file.fromWorkspacePath.toLowerCase().includes(searchString)
      )
    }).reverse().slice(0, 4)

    activeId = filteredFiles.length - 1;
  }





  // if (atableFiles.length < 1) throw new Error("no available agents");
  function handleKeyDown(e: KeyboardEvent) {
    console.log('handleKeyDown in AtDropdown')
    if (e.key === "Enter") {
      // create agent
      e.preventDefault();

      filteredFiles[activeId] && handleAddChip(filteredFiles[activeId]);
    }
    if (e.key == "ArrowDown") {
      if (activeId == filteredFiles.length - 1) activeId = 0;
      else activeId++;
    } else if (e.key == "ArrowUp") {
      if (activeId == 0) activeId = filteredFiles.length - 1;
      else activeId--;
    } else return;
  }

</script>

<svelte:window on:keydown={handleKeyDown} />

{#if filteredFiles.length}
<div
  class="absolute bottom-full left-0 px-2 w-full z-20 drop-shadow-[0_-4px_16px_0px_rgba(0,0,0,0.36)]"
>
  {#each filteredFiles as file, index}
    <AtDropdownCard focused={index === activeId} displayName={file.fileName} description={file.fromWorkspacePath} onClick={() => handleAddChip(file)} />
  {/each}
</div>
{/if}
