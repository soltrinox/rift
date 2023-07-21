<script lang="ts">
  import EllipsisSvg from "./icons/EllipsisDarkSvg.svelte";
  import Logs from "./logs/Logs.svelte";
  import { state } from "./stores";
  import {
    type AgentRegistryItem,
    type AgentProgress,
    WebviewState,
  } from "../../src/types";
  import Header from "./Header.svelte";
  import Chat from "./chat/Chat.svelte";
  import OmniBar from "./chat/OmniBar.svelte";
  import { onMount } from "svelte";



  let isDone = false;
  // const vscodeState = vscode.getState();
  // console.log("attempting to access vscode state:");
  // console.log(vscodeState);
  // if (vscodeState) state.set(vscodeState);

  const incomingMessage = (event: any) => {
    if(!event.data) throw new Error()
    console.log("ChatWebview event.data.type:", event.data.type);
    // Listen for the response

    switch (event.data.type) {

      // case "listAgents":
        // console.log("new agents just dropped");
        // console.log(event.data.data);
        // agentRegistry = event.data.data;
        // //TODO store available agents
        // // state.update((state) => ({
        // //   ...state,
        // //   availableAgents: agentRegistry,
        // // }));
        // console.log("availableAgents in state" + JSON.stringify(agentRegistry));
        // throw new Error('old state stuff')
        // break;

      default:
        console.log("no case matched for:", event.data.type, "in ChatWebview");
      // throw new Error("no case matched: " + event.data);
    }
  };
</script>

<!-- <svelte:window on:message={incomingMessage} /> -->

<div class="h-screen flex flex-col">
  <!-- <Header /> -->
  <Chat />
  <OmniBar />
</div>
