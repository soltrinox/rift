export type ChatAgentProgress = {
    id: number,
    response: string
    log?: {
        message: string,
        severity: string
    }
    done: boolean
};


export type Agent = {
    id: number
};


export type SvelteStore = {
    history: { role: "user" | "assistant", content: string }[],
    agents: Agent[],
    logs: ChatAgentProgress[],
};