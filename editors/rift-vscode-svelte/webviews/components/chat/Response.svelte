<script lang='ts'>
  import RiftSvg from "../icons/RiftSvg.svelte";
  export let hasSvg = false;
  export let value = ''
  export let isNew = false
  import {loading} from '../stores'
  console.log($loading)
</script>

<div class='w-full text-md p-2 focus:outline-none min-h-8 flex flex-row'>
  {#if hasSvg}
    <RiftSvg />
  {/if}
  <div id='response' class='w-full text-md min-h-8'> 
  {
  (isNew && $loading) ? '...' : value
  }
  </div>
</div>
