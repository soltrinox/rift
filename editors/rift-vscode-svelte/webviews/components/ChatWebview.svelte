<!-- Navbar.svelte -->
<script lang="ts">
  import EllipsisSvg from "./icons/EllipsisDarkSvg.svelte";
  import Logs from "./logs/Logs.svelte";
  import { DEFAULT_STATE, loading, state } from "./stores";
  import type { ChatAgentProgress, AgentRegistryItem, AgentProgress, AgentChatRequest, AgentInputRequest, AgentResult, AgentUpdate } from "../../src/types";
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
    vscode.postMessage({
        type: "runAgent",
        params: {
          agent_type: 'rift_chat',
          agent_params: {}, 
        },
      });
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
        console.log("ChatWebview event.data.type:",event.data.type);
        // Listen for the response
        
        switch (event.data.type) {
            case "input_request": 
                const input_request = event.data.data as AgentInputRequest;
                let agentId = input_request.agent_id;
                let status = input_request.tasks.task.status;
                break;
            case "selectedAgentId":
                console.log(`chatwebview selectedAgentId: ${event.data.data}`);
                state.update((state) => ({
                  ...state,
                  selectedAgentId: event.data.data,
                }));

                // TODO: focus the selected agent
            case "chatProgress":
              const progress = event.data.data as ChatAgentProgress;
              const agentId = progress.id; //FIXME brent HARDCODED change later
              progressResponse = progress.response;
              // console.log(progressResponse);
              isDone = progress.done;
                      break;
                  
            case "chat_request": 
                const chat_request = event.data.data as AgentChatRequest;
                break;
            
            case "update": 
                const update = event.data.data as AgentUpdate;
                break;
            
            case "result":
                const result = event.data.data as AgentResult;
            
                break;
            
            case "progress": {
                let progress = event.data.data as AgentProgress;
                let agentId = progress.agent_id;
                let status = progress.tasks.task.status;

                // if there's no currently selected agent. set this as the currently selected agent.
                state.update(prevState => {
                  return (
                    {
                      ...prevState,
                      agents: {
                        ...prevState.agents,
                        [agentId]: {
                          ...prevState.agents[agentId],
                          
                        }
                      }
                    }
                  )
                })
                

                // for sticky window^
                if (status == "done") {
                    state.update((state) => ({
                        ...state,
                        agents: {
                            ...state.agents,
                            [agentId]: {
                                ...state.agents[agentId],
                                chatHistory: [
                                    ...state.agents[agentId].chatHistory,
                                    {
                                        role: "assistant",
                                        content: progressResponse,
                                    },
                                ],
                                tasks: state.agents[agentId].tasks,
                            },
                        },
                    }));
                    loading.set(false);
                    progressResponse = "";
                }
            
                break;
            
            default:
                console.log('no case matched for:', event.data.type, 'in LogWebview')
                // throw new Error("no case matched: " + event.data);
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
