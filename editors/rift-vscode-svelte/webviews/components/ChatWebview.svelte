<!-- Navbar.svelte -->
<script lang="ts">
  import EllipsisSvg from "./icons/EllipsisDarkSvg.svelte";
  import Logs from "./logs/Logs.svelte";
  import { DEFAULT_STATE, loading, state } from "./stores";
  import type { ChatAgentProgress, AgentRegistryItem } from "../../src/types";
  import Header from "./Header.svelte";
  import Chat from "./chat/Chat.svelte";
  import OmniBar from "./chat/OmniBar.svelte";
  import { onMount } from "svelte";

  // UNCOMMENT THE BELOW LINE AND REFRESH IF YOU NEED A HARD RESET:
  console.log("RESETTING VSCODE STATE");
  console.log(DEFAULT_STATE);
  vscode.setState(DEFAULT_STATE);
  console.log(vscode.getState());

  onMount(() => {
    //response is saved to state in ChatWebview.svelte
    //get initial list of agents
    vscode.postMessage({ type: "listAgents" });
  });

  state.subscribe((state) => {
    console.log("saving state");
    if (JSON.stringify(state) != JSON.stringify(DEFAULT_STATE)) {
      vscode.setState(state);
    }
  });
  let agentRegistry: AgentRegistryItem[] = [];
  let isDone = false;
  const vscodeState = vscode.getState();
  console.log("attempting to access vscode state:");
  console.log(vscodeState);
  if (vscodeState) state.set(vscodeState);
  let progressResponse: string;
  const incomingMessage = (event: any) => {
    // Listen for the response

    switch (event.data.type) {
      case "chatProgress":
        const progress = event.data.data as ChatAgentProgress;
        const agentId = progress.id; //FIXME brent HARDCODED change later
        progressResponse = progress.response;
        // console.log(progressResponse);
        isDone = progress.done;

        // const randomLogSeverity = ["done", "progress"];
        // let random = Math.floor(Math.random() * randomLogSeverity.length);
        // // const randomLogMessage = [
        //   "Things are going great",
        //   "making progress",
        //   "uh oh",
        //   "something else",
        // ];
        // let random2 = Math.floor(Math.random() * randomLogMessage.length);

        // for sticky window^
        if (isDone) {
          state.update((state) => ({
            ...state,
            agents: {
              ...state.agents,
              [agentId]: {
                ...state.agents[agentId],
                chatHistory: [
                  ...state.agents[agentId].chatHistory,
                  { role: "assistant", content: progressResponse },
                ],
              },
            },
          }));
          loading.set(false);
          progressResponse = "";
        }
        break;
      case "agents":
        console.log("new agents just dropped");
        console.log(event.data.data);
        agentRegistry = event.data.data;
        //TODO store available agents
        state.update((state) => ({
          ...state,
          availableAgents: agentRegistry,
        }));
        console.log("availableAgents in state" + JSON.stringify(agentRegistry));
        break;
      // case "chat_request":
      //   console.log("chat_request");
      //   console.log(event.data.data);
      //   break;
      default:
        throw new Error("no case matched" + event.data);
    }
  };
</script>

<svelte:window on:message={incomingMessage} />

<div class="h-screen">
  <Header />
  <div style="height: calc(100% - 80px);" class="overflow-y-auto">
    <Chat {progressResponse} />
  </div>
  <div style="bottom: 0px; position: absolute" class="w-full">
    <OmniBar />
  </div>
</div>
