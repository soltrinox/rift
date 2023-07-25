<script lang="ts">
  import SendSvg from "../icons/SendSvg.svelte";
  import { state } from "../stores";
  import type { WebviewState } from "../../../src/types";
  import UserSvg from "../icons/UserSvg.svelte"
  export let value: string = "";

  let textarea: HTMLDivElement; //used to be a textarea

  // $: {
  //   if (textarea) {
  //     textarea.style.height = "auto";
  //     textarea.style.height = textarea.scrollHeight + "px";
  //   }
  // }

</script>

<div class="bg-[var(--vscode-input-background)] w-full py-[8px] px-[13px]">
  <div class="flex items-center pb-[6px]">
    <UserSvg classes='mr-2' />
    <p class="text-sm font-semibold">YOU</p>
  </div>
  <div class="text-md flex flex-row items-center">
    <div
      bind:this={textarea}
      >
      {value}
    </div>
  </div>
</div>
