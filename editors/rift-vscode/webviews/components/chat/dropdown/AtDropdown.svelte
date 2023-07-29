<script lang="ts">
  import { state } from "../../stores"
  import type { AtableFile } from "../../../../src/types"
  import AtDropdownCard from "./AtDropdownCard.svelte"

  // state.subscribe(s => console.log('rOFiles',s.files.recentlyOpenedFiles))

  // this will be the latest @ to the end of the textbox, not including already made chips. if no matches show up then the user will be able to keep typing and the dropdown won't appear.
  export let editorContent:string = ''
  let latestAtToEndOfTextarea: string |undefined= editorContent.lastIndexOf("@") > -1 ? editorContent.slice(editorContent.lastIndexOf("@")) : undefined
  export let handleAddChip: (file: AtableFile) => void
  
  
  let atableFiles = Array.from(new Set([...$state.files.recentlyOpenedFiles, ...$state.files.nonGitIgnoredFiles]))
  $: console.log('af:', atableFiles)
  let filteredFiles = atableFiles
  let activeId = atableFiles.length - 1
  

  
  $: {
    console.log('editorContent:',editorContent)
    latestAtToEndOfTextarea = editorContent.lastIndexOf("@") > -1 ? editorContent.slice(editorContent.lastIndexOf("@")) : undefined
    console.log('lateota:', latestAtToEndOfTextarea)
    console.log('af', atableFiles)
    console.log('files',$state.files)
    filteredFiles = Array.from(new Set([...$state.files.recentlyOpenedFiles, ...$state.files.nonGitIgnoredFiles]))
      .filter((file) => {
        let searchString = latestAtToEndOfTextarea?.substring(1).toLowerCase() ?? ''
        return (
          file.fileName.toLowerCase().includes(searchString) ||
          file.fromWorkspacePath.toLowerCase().includes(searchString)
        )
      })
      .reverse()
      .slice(0, 4)

    activeId = filteredFiles.length - 1
    console.log('FF,',filteredFiles)
  }

  // if (atableFiles.length < 1) throw new Error("no available agents");

  function handleKeyDown(e: KeyboardEvent) {
    console.log("handleKeyDown in AtDropdown, ",filteredFiles[activeId])
    // if (e.key === "Enter") {
    //   e.preventDefault()
    //   // create agent
    //   if (!filteredFiles[activeId]) {
    //     console.log("filteredFiles")
    //     console.log(filteredFiles)
    //     console.log("activeId")
    //     console.log(activeId)
    //     throw new Error("attempting to add a chip that is not in filtered files")
    //   }
    //   console.log('adding chip for', filteredFiles[activeId].fileName)
    //   handleAddChip(filteredFiles[activeId])
    // }
    if (e.key == "ArrowDown") {
      // e.preventDefault()
      if (activeId == filteredFiles.length - 1) activeId = 0
      else activeId++
      console.log("new active Id: ", activeId)
    } else if (e.key == "ArrowUp") {
      // e.preventDefault()
      if (activeId == 0) activeId = filteredFiles.length - 1
      else activeId--
      console.log("new active Id: ", activeId)
    } else return
  }

  $: {
    if (!filteredFiles[activeId] && latestAtToEndOfTextarea && activeId != -1) {
      console.log("filteredFiles")
      console.log(filteredFiles)
      console.log("activeId")
      console.log(activeId)
      throw new Error("active id set to something else")
    }
  }
</script>

<svelte:window on:keydown={handleKeyDown} />

{#if filteredFiles.length && latestAtToEndOfTextarea != undefined}
  <div class="absolute bottom-full left-0 px-2 w-full z-20 drop-shadow-[0_-4px_16px_0px_rgba(0,0,0,0.36)]">
    {#each filteredFiles as file, index}
      <AtDropdownCard
        focused={index === activeId}
        displayName={file.fileName}
        description={file.fromWorkspacePath}
        onClick={() => handleAddChip(file)} />
    {/each}
  </div>
{/if}
