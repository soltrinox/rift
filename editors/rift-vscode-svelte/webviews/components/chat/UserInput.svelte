<script lang="ts">
  import SendSvg from "../icons/SendSvg.svelte";
  import UserSvg from "../icons/UserSvg.svelte";
  import { state } from "../stores";
  import type { WebviewState } from "../../../src/types";
  export let value: string = "";

  let textarea: HTMLTextAreaElement;

  $: {
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = textarea.scrollHeight + "px";
    }
  }
</script>

<div class="bg-[var(--vscode-input-background)] w-full p-2">
  <div class="flex items-center py-1">
    <UserSvg size={12} />
    <p class="text-sm">YOU</p>
  </div>
  <div class="w-full text-md flex flex-row items-center">
    <textarea
      bind:this={textarea}
      class="w-full block outline-none focus:outline-none bg-transparent resize-none hide-scrollbar"
      placeholder="Type to chat or hit / for commands"
      disabled={true}
      {value}
      rows="1"
    />
  </div>
</div>

<style>
  .hide-scrollbar::-webkit-scrollbar {
    display: none;
  }

  .hide-scrollbar {
    -ms-overflow-style: none; /* IE and Edge */
    scrollbar-width: none; /* Firefox */
  }
</style>
