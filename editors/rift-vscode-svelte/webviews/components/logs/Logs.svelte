<script lang="ts">
    import { loading, state } from "../stores";
    import Log from "./Log.svelte";
    import Agent from "./Agent.svelte";
</script>

<div>
    <div class="ml-3">
        <h1>Rift Logs</h1>
        <Agent color="yellow" title="gpt-engineer" />
        <Agent color="green" title="rift-code-improve" />
        <Agent color="red" title="smol-dev" />
        <Agent color="green" title="rift-chat" />
    </div>
</div>
