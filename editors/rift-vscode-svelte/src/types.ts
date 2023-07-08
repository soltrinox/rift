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
    //    logs: { role: "user" | "assistant", content: string }[]
}