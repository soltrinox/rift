<script lang="ts">
    import { createEventDispatcher, onMount } from "svelte";
    import LogGreenSvg from "../icons/LogGreenSvg.svelte";
    import LogYellow from "../icons/LogYellowSvg.svelte";
    import LogRed from "../icons/LogRedSvg.svelte";
    import type { Log } from "../../../src/types";
    export let log: Log;
    export let id: string;

    const dispatch = createEventDispatcher();

    onMount(async () => {
        if (log.severity == "done") {
            dispatch("message", {
                done: `${id}-done`,
            });
        }
    });
</script>

<a class="flex select-none">
    <div class="ml-6 border-l-4" />
    {#if log.severity == "done"}
        <div class="ml-4 mr-2 mt-0.5"><LogGreenSvg /></div>
    {:else}
        <div class="ml-4 mr-2 mt-0.5"><LogYellow /></div>
        <!-- {:else}
        <div class="ml-4 mr-2 mt-0.5"><LogRed /></div>
    {/if} -->
    {/if}
    {log?.message.substring(0, 40)}
</a>
