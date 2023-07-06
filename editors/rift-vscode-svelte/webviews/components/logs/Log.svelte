<script lang="ts">
    import LogGreenSvg from "../icons/LogGreenSvg.svelte";
    import LogYellow from "../icons/LogYellowSvg.svelte";
    import LogRed from "../icons/LogRedSvg.svelte";
    import type { ChatAgentProgress } from "../../../src/types";
    export let progress: ChatAgentProgress;
</script>

<a class="flex select-none">
    <div class="ml-6 border-l-4" />
    {#if progress.done == true}
        <div class="ml-4 mr-2 mt-0.5"><LogGreenSvg /></div>
    {:else}
        <div class="ml-4 mr-2 mt-0.5"><LogYellow /></div>
        <!-- {:else}
        <div class="ml-4 mr-2 mt-0.5"><LogRed /></div>
    {/if} -->
    {/if}
    {progress.response.substring(0, 40)}
</a>
