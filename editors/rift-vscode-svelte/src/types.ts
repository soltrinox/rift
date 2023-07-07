export type ChatAgentProgress = {
    id: number,
    response: string
    log?: Log
    done: boolean
};


export type Log = {
    message: string,
    severity: string
}

type ChatMessage = { role: "user" | "assistant", content: string }

type Agent = {
    chatHistory: ChatMessage[]
    logs: Log[]
    description: string
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
    currentlySelectedAgentId: string,
    agents: {
        [id: string]: Agent
    }
    //    logs: { role: "user" | "assistant", content: string }[]
}