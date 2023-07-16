import type { Tasks } from "./client";

export class ChatMessage {
    constructor(
        public role: "user" | "assistant",
        public content: string
    ) { }
}

export type InputRequest = {
    msg: string;
    place_holder: string
}


export type ChatMessageType = {
    role: "user" | "assistant",
    content: string
}

export type AgentRegistryItem = {
    agent_type: string
    agent_description: string
    display_name: string
    agent_icon: string | null
}


// this is working
export type AgentProgress = {
    agent_id: string
    agent_type: string
    tasks: { subtasks: [{ description: string, status: string }] | [], task: { description: string, status: string } }
    payload: any
};


export class Agent {
    constructor(
        public type: string, // aider, gpt-engineer, etc
        public hasNotification: boolean = false,
        public chatHistory: ChatMessage[] = [],
        public inputRequest: InputRequest | null = null,
        public tasks?: Tasks
    ) { }
}

export type SvelteStore = {
    selectedAgentId: string,
    agents: {
        [id: string]: Agent
    }
    availableAgents: AgentRegistryItem[]
    //    logs: { role: "user" | "assistant", content: string }[]
}