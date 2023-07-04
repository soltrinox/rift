<script lang="ts">
    import LogGreenSvg from "../icons/LogGreenSvg.svelte";
    import LogYellow from "../icons/LogYellowSvg.svelte";
    import LogRed from "../icons/LogRedSvg.svelte";
    export let color = "green";
    export let message = "log this";
</script>

<div class="flex">
    {#if color == "green"}
        <div class="mx-2 mt-0.5"><LogGreenSvg /></div>
    {:else if color == "yellow"}
        <div class="mx-2 mt-0.5"><LogYellow /></div>
    {:else}
        <div class="mx-2 mt-0.5"><LogRed /></div>
    {/if}
    {message}
</div>
