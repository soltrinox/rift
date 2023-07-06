<script lang="ts">
    import { loading, state } from "../stores";
    import Log from "./Log.svelte";
    import Agent from "./Agent.svelte";
</script>

<div>
    <div class="ml-3">
        <h1>RIFT LOGS (WIP help welcome!)</h1>
        {#each $state.agents as agent}
            <Agent id={agent.id} name="temp agent name" />
        {/each}
    </div>
</div>
