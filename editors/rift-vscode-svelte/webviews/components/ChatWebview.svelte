<script lang="ts">
  import Header from "./Header.svelte";
  import Chat from "./chat/Chat.svelte";
  import OmniBar from "./chat/OmniBar.svelte";
  vscode.postMessage({type: "refreshState"})


</script>

<!-- <svelte:window on:message={incomingMessage} /> -->

<div class="h-screen flex flex-col">
  <!-- <Header /> -->
  <Chat />
  <OmniBar />
</div>
