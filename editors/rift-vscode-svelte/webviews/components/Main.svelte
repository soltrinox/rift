<!-- Navbar.svelte -->
<script lang="ts">
  import { onMount, onDestroy, tick } from "svelte";
  import CopySvg from "./icons/CopySvg.svelte";
  import EllipsisSvg from "./icons/EllipsisDarkSvg.svelte";
  import UserSvg from "./icons/UserSvg.svelte";
  import RiftSvg from "./icons/RiftSvg.svelte";
  import UserInput from "./chat/UserInput.svelte";
  import Response from "./chat/Response.svelte";
  import Logs from "./logs/Logs.svelte";
  import { DEFAULT_STATE, loading, state } from "./stores";
  import type { ChatAgentProgress } from "../../src/types";
  import Header from "./Header.svelte";
  import chalk from "chalk";
  import Chat from "./chat/Chat.svelte";
  
  state.subscribe((state) => {
    
    console.log('saving state')
    if(JSON.stringify(state) != JSON.stringify(DEFAULT_STATE)) {vscode.setState(state)}
  });

  let isDone = false;
  const vscodeState = vscode.getState();
  console.log("attempting to access vscode state:");
  console.log(vscodeState);
  if (vscodeState) state.set(vscodeState);
  let progressResponse: string;
  const incomingMessage = (event: any) => {
    // console.log(event);
    const progress = event.data.data as ChatAgentProgress;
    const agentId = "rift-chat"; //FIXME brent HARDCODED change later
    progressResponse = progress.response;
    // console.log(progressResponse);
    isDone = progress.done;

    const randomLogSeverity = ["done", "progress"];
    let random = Math.floor(Math.random() * randomLogSeverity.length);
    const randomLogMessage = [
      "Things are going great",
      "making progress",
      "uh oh",
      "something else",
    ];
    let random2 = Math.floor(Math.random() * randomLogMessage.length);

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
            logs: [
              ...state.agents[agentId].logs,
              {
                message: randomLogMessage[random],
                severity: randomLogSeverity[random],
              },
            ],
          },
        },
      }));
      loading.set(false);
      progressResponse = "";
    }
  };
</script>

<svelte:window on:message={incomingMessage} />

<div>
  <Header />
  <div>
    <Chat {progressResponse} />
    <div class="max-h-[30vh]">
      <section
        id="divider"
        class="border-t-2 pt-1 pb-2 hero container max-w-screen-lg mx-auto flex justify-center"
      >
        <EllipsisSvg />
      </section>
      <Logs />
    </div>
  </div>
</div>
