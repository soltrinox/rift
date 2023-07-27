<script lang="ts">
    import { state } from "../stores";
    import Agent from "./Agent.svelte";
    import type { WebviewState } from "../../../src/types";
</script>

<div>
    <div class="space-y-1">
        {#if Object.keys($state.agents).length > 0}
            {#each Object.entries($state.agents) as [key, value]}

                    <Agent
                        id={key}
                        name={value.tasks?.task.description}
                        hasNotification={value.hasNotification}
                    />

            {/each}
        {/if}
    </div>
</div>
