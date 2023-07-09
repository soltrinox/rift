export type ChatAgentProgress = {
    id: number,
    response: string
    done: boolean
};

export class ChatMessage {
    constructor(
        public role: "user" | "assistant",
        public content: string
    ) { }
}

export type AgentRegistryItem = {
    agent_type: string
    agent_description: string
    display_name: string
    agent_icon: string | null
}

export class Agent {
    constructor(
        public id: string,
        public type: string, // aider, gpt-engineer, etc
        public chatHistory: ChatMessage[] = [],
        public taskRoot: AgentTask[] = [],
    ) { }
}

class AgentTask {
    constructor(
        public id: string,
        public description: string,
        public status: "running" | "done" | "error",
        public showBadge: boolean,
        public subtasks: AgentTask[],
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