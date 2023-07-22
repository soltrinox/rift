export interface Task {
  description: string;
  status: string;
}

export interface Tasks {
  task: Task;
  subtasks: Task[];
}

export class ChatMessage {
  constructor(public role: "user" | "assistant", public content: string) { }
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
  hasNotification: boolean;
  isDeleted: boolean;
  chatHistory: ChatMessage[];
  inputRequest?: InputRequest | null;
  tasks?: Tasks;
  // isChatAgent: boolean = false;
  isStreaming: boolean = false;
  streamingText: string = ''

  constructor(type: string, hasNotification?: boolean, chatHistory?: ChatMessage[], inputRequest?: InputRequest | null, tasks?: Tasks) {
    this.type = type;
    this.hasNotification = hasNotification ?? false;
    this.isDeleted = false;
    this.chatHistory = chatHistory ?? [];
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
  //    logs: { role: "user" | "assistant", content: string }[]
};



// the only reason this is here is because types.ts is used for shared logic between the webviews and the extension.
// Do not put more shared logic in here--we shouldn't need it. If we do, we should create a shared folder and update the eslint rules for imports
export const DEFAULT_STATE: WebviewState = {
  selectedAgentId: '',
  agents: {
  },
  availableAgents: [{
    agent_type: "rift_chat",
    agent_description: '',
    agent_icon: '',
    display_name: 'Rift Chat'
  }],
}
