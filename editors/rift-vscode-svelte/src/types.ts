import type { Tasks } from "./client";

export class ChatMessage {
  constructor(public role: "user" | "assistant", public content: string) {}
}

export type InputRequest = {
  msg: string;
  place_holder: string;
};

export type ChatMessageType = {
  role: "user" | "assistant";
  content: string;
};

export type AgentRegistryItem = {
  agent_type: string;
  agent_description: string;
  display_name: string;
  agent_icon: string | null;
};

// this is working
export type AgentProgress = {
  agent_id: string;
  agent_type: string;
  tasks: {
    subtasks: [{ description: string; status: string }] | [];
    task: { description: string; status: string };
  };
  payload: any;
};

// export class Agent {
//   constructor(
//     public type: string, // aider, gpt-engineer, etc
//     public hasNotification: boolean = false,
//     public chatHistory: ChatMessage[] = [],
//     public inputRequest: InputRequest | null = null,
//     public tasks?: Tasks
//   ) {}
// }

export class WebviewAgent {
  type: string;
  hasNotification: boolean;    //TODO does this have to be nullable?
  chatHistory?: ChatMessage[];
  inputRequest?: InputRequest | null;
  tasks?: Tasks;

  constructor(type: string, hasNotification?: boolean, chatHistory?: ChatMessage[], inputRequest?: InputRequest | null, tasks?: Tasks){
    this.type = type;
    this.hasNotification = hasNotification ?? false;
    this.chatHistory = chatHistory;
    this.inputRequest = inputRequest;
    this.tasks = tasks;
  }
}


export type WebviewState = {
  selectedAgentId: string;
  agents: {
    [id: string]: WebviewAgent;
  };
  availableAgents: AgentRegistryItem[];
  isStreaming: boolean;
  streamingText: string //FIXME should just be able to update the last ChatMessage of an agent's chat history
  //    logs: { role: "user" | "assistant", content: string }[]
};


