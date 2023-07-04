<script lang="ts">
    import { loading, state } from "../stores";
    import Log from "./Log.svelte";
    import Agent from "./Agent.svelte";
    export let chatDone = false;
</script>

<div>
    <div class="ml-3">
        <h1>Rift Logs</h1>

        <Agent done={chatDone} title="rift-chat" />
    </div>
</div>
