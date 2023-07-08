<!-- Navbar.svelte -->
<script lang="ts">
  import EllipsisSvg from "./icons/EllipsisDarkSvg.svelte";
  import Logs from "./logs/Logs.svelte";
  import { DEFAULT_STATE, loading, state } from "./stores";
  import type { ChatAgentProgress } from "../../src/types";
  import Header from "./Header.svelte";
  import Chat from "./chat/Chat.svelte";
  import OmniBar from "./chat/OmniBar.svelte"
  
  state.subscribe((state) => {
    
    console.log('saving state')
    // UNCOMMENT THE BELOW LINE AND REFRESH IF YOU NEED A HARD RESET:
    vscode.setState(DEFAULT_STATE)
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
    const agentId = Object.values(DEFAULT_STATE.agents).find(agent => agent.type == 'rift-chat')?.id || 'deadb33f'; //FIXME brent HARDCODED change later
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
              ...state.agents[agentId].taskRoot,
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
    <OmniBar />
    <div class="max-h-[30vh]">
      <section
        id="divider"
        class="pt-1 pb-2 hero container max-w-screen-lg mx-auto flex justify-center"
      > 
        <EllipsisSvg />
      </section>
      <Logs />
    </div>
  </div>
</div>
