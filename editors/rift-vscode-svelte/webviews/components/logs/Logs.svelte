<script lang="ts">
    import { loading, state } from "../stores";
    import Log from "./Log.svelte";
    import Agent from "./Agent.svelte";
</script>

<div>
    <div class="ml-3">
        <h1 class="font-bold">RIFT LOGS</h1>
        {#each Object.entries($state.agents) as [key, value]}
            <Agent id={key} name="rift-chat" />
        {/each}
    </div>
</div>
