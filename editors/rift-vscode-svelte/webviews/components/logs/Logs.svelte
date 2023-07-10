<script lang="ts">
    import { loading, state } from "../stores";
    import Log from "./Log.svelte";
    import Agent from "./Agent.svelte";
    import type { AgentType, SvelteStore } from "../../../src/types";
    import { onMount } from "svelte";
    let store: SvelteStore;
    state.subscribe((s) => {
        store = s;
    });
</script>

<div>
    <div class="ml-3 mt-2">
        {#each Object.entries(store.agents) as [key, value]}
            <Agent id={key} name={value.tasks.task.description} />
        {/each}
    </div>
</div>
