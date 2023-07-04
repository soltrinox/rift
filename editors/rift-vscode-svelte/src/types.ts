export type ChatAgentProgress = {
    id: number,
    response: string
    log?: {
        message: string,
        severity: string
    }
    done: boolean
}

export type SvelteStore = {
    history: { role: "user" | "assistant", content: string }[]
    logs: { role: "user" | "assistant", content: string }[]
}