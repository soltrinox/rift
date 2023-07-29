<script lang="ts">
  // This script imports the necessary components and state for the ChatWebview.
  // It also posts a message to vscode to refresh the state.

  // Import the AcceptRejectBar component.
  import AcceptRejectBar from "./AcceptRejectBar.svelte";
  // Import the Chat component.
  import Chat from "./chat/Chat.svelte";
  // Import the OmniBar component.
  import OmniBar from "./OmniBar.svelte";
  // Import the state from the stores.
  import { state } from "./stores";
  // Post a message to vscode to refresh the state.
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
</div>
