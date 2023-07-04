<script lang="ts">
    import LogGreenSvg from "../icons/LogGreenSvg.svelte";
    import LogYellow from "../icons/LogYellowSvg.svelte";
    import LogRed from "../icons/LogRedSvg.svelte";
    export let color = "green";
    export let message = "log this";
</script>

<div class="flex">
    <div class="ml-6 border-l-4" />
    {#if color == "green"}
        <div class="ml-4 mr-2 mt-0.5"><LogGreenSvg /></div>
    {:else if color == "yellow"}
        <div class="ml-4 mr-2 mt-0.5"><LogYellow /></div>
    {:else}
        <div class="ml-4 mr-2 mt-0.5"><LogRed /></div>
    {/if}
    {message}
</div>
