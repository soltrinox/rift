import * as vscode from 'vscode'
import {
    LanguageClient,
    LanguageClientOptions,
    ServerOptions,
    Executable,
    TransportKind,
    StreamInfo,
    TextDocumentPositionParams,
    NotificationType,
    TextDocumentIdentifier,
    State,
} from 'vscode-languageclient/node'

export type ChatAgentProgress = {
    id: string,
    response: string
    done: boolean
}; 


export interface RunAgentParams {
    agent_type: string
    agent_params: any
}



export interface RunChatParams {
    message: string
    messages: { // does not include latest message
        role: string,
        content: string
    }[],
    // position: vscode.Position,
    // textDocument: TextDocumentIdentifier,
}

export interface RunAgentResult {
    id: string
}

export interface RunAgentSyncResult {
    id: number
    text: string
}

export type AgentStatus = 'running' | 'done' | 'error' | 'accepted' | 'rejected'

export interface RunAgentProgress {
    id: number
    textDocument: TextDocumentIdentifier
    log?: {
        severity: string;
        message: string;
    }
    cursor?: vscode.Position
    /** This is the set of ranges that the agent has added so far. */
    ranges?: vscode.Range[]
    status: AgentStatus
}

export interface Task {
    description: string, status: string,
}

export interface Tasks {
    task: Task
    subtasks: Task[]
}

export interface AgentProgress {
    agent_id: string,
    agent_type: string,
    tasks: Tasks,
    payload: any,
}

export interface Task {
    description: string, status: string,
}

export interface Tasks {
    task: Task
    subtasks: Task[]
}

export class ChatMessage {
    constructor(
        public role: "user" | "assistant",
        public content: string
    ) { }
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




//FIXME fill these out!
export type AgentResult = unknown
export type AgentUpdate = unknown
export type AgentChatRequest = unknown
export type AgentInputRequest = unknown



export class Agent {
    constructor(
        public type: string, // aider, gpt-engineer, etc
        public chatHistory: ChatMessage[] = [],
        public tasks: Tasks
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