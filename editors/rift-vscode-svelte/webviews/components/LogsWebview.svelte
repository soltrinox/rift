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

    let agentRegistry: AgentRegistryItem[] = [];

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
    let agentOptions: { type: string; description?: string; svg?: string }[] = [
        //TODO get from server
        { type: "rift-chat", description: "ask me anything ab life bro" },
        { type: "aider", description: "congrats ur now a 10x engineer" },
        { type: "gpt-engineer", description: "an engineer but gpt" },
        { type: "auto-code-review", description: "code review but meaner" },
        { type: "repl-auto-debug", description: "let me debug for u" },
    ];
    let isDone = false;
    const vscodeState = vscode.getState();
    console.log("attempting to access vscode state:");
    console.log(vscodeState);
    if (vscodeState) state.set(vscodeState);
    let progressResponse: string;
    const incomingMessage = (event: any) => {
        // Listen for the response

        switch (event.data.type) {
            case "tasks": {
            } // TODO
            case "progress":
                const progress = event.data.data as ChatAgentProgress;
                const agentId = "deadb33f2"; //FIXME brent HARDCODED change later
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
                                    {
                                        role: "assistant",
                                        content: progressResponse,
                                    },
                                ],
                                taskRoot: [...state.agents[agentId].taskRoot],
                            },
                        },
                    }));
                    loading.set(false);
                    progressResponse = "";
                }
                break;
            default:
                throw new Error("no case matched");
        }
    };
</script>

<svelte:window on:message={incomingMessage} />

<div class="">
    <div>
        <Logs />
    </div>
</div>
