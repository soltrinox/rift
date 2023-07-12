<!-- Navbar.svelte -->
<script lang="ts">
    import EllipsisSvg from "./icons/EllipsisDarkSvg.svelte";
    import Logs from "./logs/Logs.svelte";
    import { DEFAULT_STATE, loading, state } from "./stores";
    import type { AgentRegistryItem } from "../../src/types";
    import Header from "./Header.svelte";
    import Chat from "./chat/Chat.svelte";
    import OmniBar from "./chat/OmniBar.svelte";
    import { onMount } from "svelte";
    import type {AgentInputRequest, AgentChatRequest, AgentUpdate, AgentResult, AgentProgress} from '../../src/client'
    let agentRegistry: AgentRegistryItem[] = [];

    // UNCOMMENT THE BELOW LINE AND REFRESH IF YOU NEED A HARD RESET:
    console.log("RESETTING VSCODE STATE");
    console.log(DEFAULT_STATE);
    vscode.setState(DEFAULT_STATE);
    console.log(vscode.getState());

    // state.subscribe((state) => {
    //     console.log("saving state");
    //     if (JSON.stringify(state) != JSON.stringify(DEFAULT_STATE)) {
    //         vscode.setState(state);
    //     }
    // });
    
    // let agentOptions: { type: string; description?: string; svg?: string }[] = [
    //     //TODO get from server
    //     { type: "rift-chat", description: "ask me anything ab life bro" },
    //     { type: "aider", description: "congrats ur now a 10x engineer" },
    //     { type: "gpt-engineer", description: "an engineer but gpt" },
    //     { type: "auto-code-review", description: "code review but meaner" },
    //     { type: "repl-auto-debug", description: "let me debug for u" },
    // ];
    let isDone = false;
    const vscodeState = vscode.getState();
    console.log("attempting to access vscode state:");
    console.log(vscodeState);
    if (vscodeState) state.set(vscodeState);
    let progressResponse: string;
    const incomingMessage = (event: any) => {
        console.log("LogsWebview event.data.type: " + event.data.type);
        console.log(
            "LogsWebview event.data.type: \n" + JSON.stringify(event.data)
        );
        // Listen for the response
        switch (event.data.type) {
            case "selectedAgentId":
                console.log(`selectedAgentId: ${event.data.data}`);
                state.update((state) => ({
                    ...state,
                    selectedAgentId: event.data.data.selectedAgentId,
                }));
            case "input_request": {
                const input_request = event.data.data as AgentInputRequest;
                // let agentId = input_request.agent_id;
                // let status = input_request.tasks.task.status;

                break;
            }
            case "chat_request": 
                const chat_request = event.data.data as AgentChatRequest;
                break;
            
            case "update": 
                const update = event.data.data as AgentUpdate;
                break;
            
            case "result": 
                const result = event.data.data as AgentResult;
                break;
            
            case "progress": 
                let progress = event.data.data as AgentProgress;
                let agentId = progress.agent_id;
                let status = progress.tasks.task.status;

                console.log("Before update");
                console.log($state);

                state.update((state) => ({
                    ...state,
                    agents: {
                        ...state.agents,
                        [agentId]: {
                            ...state.agents[agentId],
                            type: progress.agent_type,
                            tasks: progress.tasks,
                        },
                    },
                }));


                console.log("After update");
                console.log($state);

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
                const notImportant = ['listAgents']
                if(notImportant.includes(event.data.type)) return
                
                console.log('no case matched for:', event.data.type, 'in LogWebview')
                // throw new Error("no case matched: " + event.data);
        }
    };
</script>

<svelte:window on:message={incomingMessage} />

<div class="">
    <div>
        <Logs />
    </div>
</div>
