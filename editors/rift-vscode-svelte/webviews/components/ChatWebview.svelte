<script lang="ts">
  import Chat from "./chat/Chat.svelte";
  import OmniBar from "./chat/OmniBar.svelte";
  vscode.postMessage({type: "refreshState"})


</script>

<div class="h-screen flex flex-col">
  <Chat />
  <OmniBar />
</div>
