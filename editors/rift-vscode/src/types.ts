import type * as vscode from "vscode";
import type {TextDocumentIdentifier} from "vscode-languageclient/node";

export interface Task {
  description: string;
  status: CodeLensStatus | AgentStatus;
}

export interface Tasks {
  task: Task;
  subtasks: Task[];
}

// export class ChatMessage {
//   constructor(
//     public role: "user" | "assistant",
//     public content: string,
//   ) {}
// }

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
  isDeleted: boolean = false;
  chatHistory: ChatMessage[];
  inputRequest?: InputRequest | null;
  tasks?: Tasks;
  // isChatAgent: boolean = false;
  isStreaming: boolean = false;
  streamingText: string = "";
  doesShowAcceptRejectBar: boolean = false;

  constructor(
    type: string,
    hasNotification?: boolean,
    chatHistory?: ChatMessage[],
    inputRequest?: InputRequest | null,
    tasks?: Tasks,
  ) {
    this.type = type;
    this.hasNotification = hasNotification ?? false;
    this.chatHistory = chatHistory ?? [];
    this.inputRequest = inputRequest;
    this.tasks = tasks;
  }
}

export type WebviewState = {
  selectedAgentId: string;
  isFocused: boolean;
  agents: {
    [id: string]: WebviewAgent;
  };
  availableAgents: AgentRegistryItem[];
  files: {
    recentlyOpenedFiles: AtableFile[];
    nonGitIgnoredFiles: AtableFile[];
  };
};

// the only reason this is here is because types.ts is used for shared logic between the webviews and the extension.
// Do not put more shared logic in here--we shouldn't need it. If we do, we should create a shared folder and update the eslint rules for imports
export const DEFAULT_STATE: WebviewState = {
  selectedAgentId: "",
  isFocused: false,
  agents: {},
  availableAgents: [
    {
      agent_type: "rift_chat",
      agent_description: "",
      agent_icon: "",
      display_name: "Rift Chat",
    },
  ],
  files: {
    recentlyOpenedFiles: [],
    nonGitIgnoredFiles: [],
  },
};

export type OptionalTextDocument = {
  uri: string;
  version: number;
} | null


export interface AgentParams {
  agent_type: string;
  agent_id: string | null
  position: vscode.Position | null
  selection: vscode.Selection | null
  textDocument: OptionalTextDocument
  workspaceFolderPath: string | null
}

export interface RunChatParams {
  message: string;
  messages: {
    // does not include latest message
    role: string;
    content: string;
  }[];
}

export interface RunAgentResult {
  id: string;
}

export type AgentStatus =
  | "running"
  | "done"
  | "error"
  | "accepted"
  | "rejected";

export type CodeLensStatus =
  | "running"
  | "ready"
  | "accepted"
  | "rejected"
  | "error"
  | "done";

export interface RunAgentProgress {
  id: number;
  textDocument: TextDocumentIdentifier;
  log?: {
    severity: string;
    message: string;
  };
  cursor?: vscode.Position;
  /** This is the set of ranges that the agent has added so far. */
  ranges?: vscode.Range[];
  status: AgentStatus;
}

export type ChatAgentPayload =
  | {
    response?: string;
    done_streaming?: boolean;
  }
  | undefined;

export interface AgentProgress<T = any> {
  agent_id: string;
  agent_type: string;
  tasks: Tasks;
  payload: T | undefined;
}

export type ChatAgentProgress = AgentProgress<ChatAgentPayload>;

export interface AgentIdParams {
  id: string;
}

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  name?: null | string | undefined;
  editorContentString?: string; //there on user
};

export interface AgentChatRequest {
  messages: ChatMessage[];
}

export interface AgentInputRequest {
  msg: string;
  place_holder: string;
}

export interface AgentInputResponse {
  response: string;
}

export interface AgentUpdate {
  msg: string;
}
export type AgentResult = {
  id: string;
  type: string;
}; //is just an ID rn

export type AtableFile = {
  fileName: string; //example.ts
  fullPath: string; //Users/brent/dev/project/src/example.ts
  fromWorkspacePath: string; //project/src/example.ts
};
