<script lang="ts">
  import AcceptRejectBar from "./AcceptRejectBar.svelte";
  import Chat from "./chat/Chat.svelte";
  import OmniBar from "./OmniBar.svelte";
  vscode.postMessage({type: "refreshState"})


</script>

<div class="h-screen flex flex-col">
  <Chat />
  <AcceptRejectBar/>
  <OmniBar />
</div>
