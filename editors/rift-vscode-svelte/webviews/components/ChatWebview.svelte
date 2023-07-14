<script lang="ts">
  import EllipsisSvg from "./icons/EllipsisDarkSvg.svelte";
  import Logs from "./logs/Logs.svelte";
  import { DEFAULT_STATE, loading, state, progressResponse } from "./stores";
  import {
    type AgentRegistryItem,
    type AgentProgress,
    Agent,
  } from "../../src/types";
  import Header from "./Header.svelte";
  import Chat from "./chat/Chat.svelte";
  import OmniBar from "./chat/OmniBar.svelte";
  import { onMount } from "svelte";
  import type {
    AgentChatRequest,
    AgentInputRequest,
    AgentResult,
    AgentUpdate,
    ChatAgentProgress,
  } from "../../src/client";
  import { IncomingMessage } from "http";

  // UNCOMMENT THE BELOW LINES AND REFRESH IF YOU NEED A HARD RESET:
  console.log("RESETTING VSCODE STATE");
  console.log(DEFAULT_STATE);
  vscode.setState(DEFAULT_STATE);
  console.log(vscode.getState());

  onMount(() => {
    vscode.postMessage({
      type: "runAgent",
      params: {
        agent_type: "rift_chat",
        agent_params: {},
      },
    });
    //get initial list of agents
    vscode.postMessage({ type: "listAgents" });
  });

  state.subscribe((state) => {
    console.log("saving state:");
    console.log(state);
    if (JSON.stringify(state) != JSON.stringify(DEFAULT_STATE)) {
      vscode.setState(state);
    }
  });

  loading.subscribe((loading) => console.log("loading:", loading));
  let agentRegistry: AgentRegistryItem[] = [];
  let isDone = false;
  const vscodeState = vscode.getState();
  console.log("attempting to access vscode state:");
  console.log(vscodeState);
  if (vscodeState) state.set(vscodeState);

  const incomingMessage = (event: any) => {
    console.log("ChatWebview event.data.type:", event.data.type);
    // Listen for the response

    switch (event.data.type) {
      case "input_request":
        const input_request = event.data.data as AgentInputRequest;
        // let agentId = input_request.agent_id;
        // let status = input_request.tasks.task.status;
        break;
      case "selectedAgentId":
        console.log(`chatwebview selectedAgentId: ${event.data.data}`);
        state.update((state) => ({
          ...state,
          selectedAgentId: event.data.data,
        }));
        document.getElementById("omnibar")?.focus();

      // TODO: focus the selected agent
      case "chatProgress": {
        //TODO deprecate?
        // console.log(event.data.data);
        // const progress = event.data.data as ChatProgress;
        // const agentId = progress.agent_id; //FIXME brent HARDCODED change later
        // progressResponse = progress.response;
        // console.log(progressResponse);
        // isDone = progress.done_streaming;
        // break;
      }
      case "chat_request": {
        const chat_request = event.data.data as AgentChatRequest | string;
        console.log("chat_request");
        console.log(chat_request);

        // this should only apply to the first message after runAgent.
        // the rest are added via the progress calls.
        if (
          typeof chat_request !== "string" &&
          $state.agents[chat_request.id]?.chatHistory.length < 1
        ) {
          if (chat_request.messages.length > 1)
            throw new Error(
              "No previous messages on client for this ID, but server is giving multiple chat messages."
            );
          state.update((prevState) => ({
            ...prevState,
            agents: {
              ...prevState.agents,
              [chat_request.id]: {
                ...prevState.agents[chat_request.id],
                chatHistory: [...chat_request.messages],
              },
            },
          }));
        }

        //dont think we need to actually do anything here b/c everything is done
        // from the result case and progress case.
        // could maybe disable sending messages until we get a chatRequest back. If we add that, it should be added later.

        break;
      }
      case "update":
        const update = event.data.data as AgentUpdate;
        break;

      case "result":
        const result = event.data.data as AgentResult;
        const agent_id = result.id;
        state.update((state) => ({
          ...state,
          selectedAgentId: result.id,
          agents: {
            ...state.agents,
            [agent_id]: new Agent(result.type),
          },
        }));
        break;

      case "progress":
        {
          console.log("progress in ChatWebview");
          let progress = event.data.data as ChatAgentProgress;
          let agentId = progress.agent_id;

          console.log(progress);
          const response = progress.payload?.response;
          response && progressResponse.set(response);

          // FIXME brent -- crucial to determine where we initalize a new agent. I'm just tryna get this set up now.
          if (progress.payload?.done_streaming) {
            if (!response) throw new Error(" done streaming but no response?");
            state.update((prevState) => {
              return {
                ...prevState,
                agents: {
                  ...prevState.agents,
                  [agentId]: {
                    agent_id: agentId,
                    agent_type: progress.agent_type,
                    ...prevState.agents[agentId],
                    tasks: progress.tasks,
                    chatHistory: [
                      ...prevState.agents[agentId].chatHistory,
                      { role: "assistant", content: response },
                    ],
                  },
                },
              };
            });
            loading.set(false);
          }
        }

        break;
      case "listAgents":
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

      default:
        console.log("no case matched for:", event.data.type, "in ChatWebview");
      // throw new Error("no case matched: " + event.data);
    }
  };
</script>

<svelte:window on:message={incomingMessage} />

<div class="h-screen">
  <Header />
  <Chat />
  <OmniBar />
</div>
