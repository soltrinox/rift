<script lang="ts">
  import { state } from "../../stores";
  import type { AgentRegistryItem, AtableFile } from "../../../../src/types";
  import AtDropdownCard from "./AtDropdownCard.svelte";
  import { onMount } from "svelte";
  import AcceptRejectBar from "../../AcceptRejectBar.svelte"
  

  // this will be the latest @ to the end of the textbox, not including already made chips. if no matches show up then the user will be able to keep typing and the dropdown won't appear.
  export let latestAtToEndOfTextarea: string = ""; 


  let atableFiles = Array.from(new Set([...$state.files.recentlyOpenedFiles, ...$state.files.nonGitIgnoredFiles]))

  let filteredFiles = atableFiles;
  let activeId = atableFiles.length - 1;

  $: {
    // filteredAgents = availableAgents.filter((agent) => {
    //   let searchString = inputValue.substring(1).toLowerCase();
    //   return (
    //     agent.agent_type.toLowerCase().includes(searchString) ||
    //     agent.display_name.toLowerCase().includes(searchString) ||
    //     agent.agent_description.toLowerCase().includes(searchString)
    //   );
    // });


    filteredFiles = atableFiles.filter(file => {
      let searchString = latestAtToEndOfTextarea.substring(1).toLowerCase()
      return (
        file.fileName.toLowerCase().includes(searchString) ||
        file.fromWorkspacePath.toLowerCase().includes(searchString)
      )
    })

    activeId = filteredFiles.length - 1;
  }



  console.log("in dropdown: ", atableFiles);
  function handleAddChip(file: AtableFile) {
    console.log('implement')
  }


  // if (atableFiles.length < 1) throw new Error("no available agents");
  function handleKeyDown(e: KeyboardEvent) {
    e.preventDefault();
    if (e.key === "Enter") {
      // create agent

      handleAddChip(filteredFiles[activeId]);
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
  {#each filteredFiles.reverse() as file, index}
    <AtDropdownCard focused={index === activeId} displayName={file.fileName} description={file.fromWorkspacePath} onClick={() => handleAddChip(file)} />
  {/each}
</div>
{/if}
