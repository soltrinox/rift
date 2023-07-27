<script lang="ts">
    import Logs from "./logs/Logs.svelte";
    vscode.postMessage({type: "refreshState"})

</script>

<div class="">
    <div>
        <Logs />
    </div>
</div>
