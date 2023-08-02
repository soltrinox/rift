<script lang="ts">
  import AcceptRejectBar from "./AcceptRejectBar.svelte";
  import Chat from "./chat/Chat.svelte";
  import OmniBar from "./OmniBar.svelte";
  import { state } from "./stores";

  vscode.postMessage({type: "refreshState"})

</script>

<!-- This is the main ChatWebview component. It displays the Chat, AcceptRejectBar (if applicable), and OmniBar components. -->
<div class="h-screen flex flex-col">
  <!-- Display the Chat component. -->
  <Chat />
  <!-- If the selected agent's state indicates that the AcceptRejectBar should be shown, display the AcceptRejectBar component. -->
  {#if $state.agents[$state.selectedAgentId]?.doesShowAcceptRejectBar}
    <AcceptRejectBar/>
  {/if}
  <!-- Display the OmniBar component. -->
  <OmniBar />
</div>
