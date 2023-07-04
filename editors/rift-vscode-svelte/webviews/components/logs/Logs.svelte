<script lang="ts">
    import { loading, state } from "../stores";
    import Log from "./Log.svelte";

    function handleClick() {}
</script>

<div>
    <h1>Rift Logs</h1>
    <Log color="green" message="test log" />
    <Log color="yellow" message="test log" />
    <Log color="red" message="test log" />
</div>
