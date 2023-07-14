<script lang="ts">
    import { state } from "../stores";
    import Agent from "./Agent.svelte";
    import type { SvelteStore } from "../../../src/types";

    let store: SvelteStore;
    state.subscribe((s) => {
        store = s;
    });
</script>

<div>
    <div class="ml-3 mt-2">
        {#if Object.keys(store.agents).length > 0}
            {#each Object.entries(store.agents) as [key, value]}
                <Agent
                    id={key}
                    name={value.tasks?.task.description}
                    hasNotification={value.hasNotification}
                    selectedId={store.selectedAgentId}
                />
            {/each}
        {/if}
    </div>
</div>
