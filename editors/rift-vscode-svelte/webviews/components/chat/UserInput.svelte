<script lang="ts">
  import SendSvg from "../icons/SendSvg.svelte";
  import UserSvg from "../icons/UserSvg.svelte";
  import { state } from "../stores";
  import type { WebviewState } from "../../../src/types";
  export let value: string = "";

  let textarea: HTMLDivElement; //used to be a textarea

  // $: {
  //   if (textarea) {
  //     textarea.style.height = "auto";
  //     textarea.style.height = textarea.scrollHeight + "px";
  //   }
  // }

</script>

<div class="bg-[var(--vscode-input-background)] w-full">
  <div class="flex items-center pr-2 pl-[18px] pt-[8px] pb-[6px]">
    <UserSvg size={12} />
    <p class="text-sm font-semibold">YOU</p>
  </div>
  <div class="text-md flex flex-row items-center mx-[16px] mb-[8px]">
    <div
      bind:this={textarea}
      >
      {value}
    </div>
  </div>
</div>
