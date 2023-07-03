<script>
  import RiftSvg from "../icons/RiftSvg.svelte";
  export let dataId = null;
  export let hasSvg = false;
  export let value = ''

</script>

<div class='w-full text-md p-2 focus:outline-none min-h-8 flex flex-row'>
  {#if hasSvg}
    <RiftSvg />
  {/if}
  <div id='response' data-id={dataId} class='w-full text-md min-h-8'>{value}</div>
</div>
