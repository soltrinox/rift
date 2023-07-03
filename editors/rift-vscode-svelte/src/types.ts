export type ChatAgentProgress = {
    id: number,
    response: string
    log?: {
        message: string,
        severity: string
    }
    done: boolean
}