<script lang="ts">
  import FileIconSvg from "../../icons/FileIconSvg.svelte"

  export let focused: boolean = false;
  export let onClick: (...args: any) => any;
  export let displayName = 'example.ts'
  export let description = '/project/server/example.ts'

  function handleKeyDown(e: KeyboardEvent) {
    console.log('in drodown handle key down')
   if(e.key === "Enter" && focused) onClick()
  }
</script>


<div class="bg-[var(--vscode-editor-background)]">
  <div
    class={`flex flex-col hover:cursor-pointer pl-2 py-2
    ${
      focused
        ? "bg-[var(--vscode-editor-hoverHighlightBackground)]"
        : "bg-[var(--vscode-editor-background)]"
    }`}
    on:click={onClick}
    on:keydown={handleKeyDown}
  >
    <div class="flex flex-row ml-[6px]">
        <FileIconSvg/>
      {displayName}
    </div>
    <div
      class="text-[var(--vscode-gitDecoration-ignoredResourceForeground)] truncate overflow-hidden ml-[2px]"
    >
      {description}
    </div>
  </div>
</div>
