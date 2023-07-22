import * as path from "path";
import type { workspace, ExtensionContext } from "vscode";
import * as vscode from "vscode";
import { ChildProcessWithoutNullStreams, spawn } from "child_process";
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
} from "vscode-languageclient/node";
import * as net from "net";
import { join } from "path";
import * as tcpPortUsed from "tcp-port-used";
import { chatProvider, logProvider } from "./extension";
import PubSub from "./lib/PubSub";
import { DEFAULT_STATE, WebviewAgent, WebviewState } from "./types";
import { Store } from "./lib/Store";

let client: LanguageClient; //LanguageClient

const DEFAULT_PORT = 7797;

// ref: https://stackoverflow.com/questions/40284523/connect-external-language-server-to-vscode-extension

// https://nodejs.org/api/child_process.html#child_processspawncommand-args-options

/** Creates the ServerOptions for a system in the case that a language server is already running on the given port. */
function tcpServerOptions(
  context: ExtensionContext,
  port = DEFAULT_PORT
): ServerOptions {
  let socket = net.connect({
    port: port,
    host: "127.0.0.1",
  });
  const si: StreamInfo = {
    reader: socket,
    writer: socket,
  };
  return () => {
    return Promise.resolve(si);
  };
}

/** Creates the server options for spinning up our own server.*/
function createServerOptions(
  context: vscode.ExtensionContext,
  port = DEFAULT_PORT
): ServerOptions {
  if (!vscode.workspace.workspaceFolders)
    throw new Error("workspace folder does not exist");
  let cwd = vscode.workspace.workspaceFolders[0].uri.path;
  // [todo]: we will supply different bundles for the 3 main platforms; windows, linux, osx.
  // there needs to be a decision point here where we decide which platform we are on and
  // then choose the appropriate bundle.
  let command = join(context.extensionPath, "resources", "lspai");
  let args: string[] = [];
  args = [...args, "--port", port.toString()];
  let e: Executable = {
    command,
    args,
    transport: { kind: TransportKind.socket, port },
    options: { cwd },
  };
  return {
    run: e,
    debug: e,
  };
}

interface RunCodeHelperParams {
  instructionPrompt: string;
  position: vscode.Position;
  textDocument: TextDocumentIdentifier;
}

export interface RunAgentParams {
  agent_type: string;
  agent_params: any;
}

export interface ChatAgentParams extends RunAgentParams {
  agent_params: {
    position: vscode.Position,
    textDocument: {
      uri: string;
      version: number;
    }
  }
}
// interface RunAgentResult {
//     id: number
//     agentId: string | null
// }

export interface RunChatParams {
  message: string;
  messages: {
    // does not include latest message
    role: string;
    content: string;
  }[];
  // position: vscode.Position,
  // textDocument: TextDocumentIdentifier,
}

export interface AgentRegistryItem {
  agent_type: string;
  agent_description: string;
  display_name: string;
  agent_icon: string | null;
}

interface RunAgentResult {
  id: string;
}

interface RunAgentSyncResult {
  id: number;
  text: string;
}

export type AgentStatus =
  | "running"
  | "done"
  | "error"
  | "accepted"
  | "rejected";

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

export interface Task {
  description: string;
  status: string;
}

export interface Tasks {
  task: Task;
  subtasks: Task[];
}


export type ChatAgentPayload = {
  response?: string,
  done_streaming?: boolean
} | undefined

export type ChatAgentProgress = AgentProgress<ChatAgentPayload>;

export interface AgentProgress<T = any> {
  agent_id: string;
  agent_type: string;
  tasks: Tasks;
  payload: T;
}

export interface AgentIdParams {
  id: string;
}

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  name?: null | string | undefined;
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

const GREEN = vscode.window.createTextEditorDecorationType({
  backgroundColor: "rgba(0,255,0,0.1)",
});

const code_completion_send_progress = async (params: any, agent: Agent) => {
  if (params.tasks) {
    //logProvider.postMessage("tasks", { agent_id: params.agent_id, ...params.tasks });
    if (params.tasks.task.status) {
      if (agent.status !== params.tasks.task.status) {
        agent.status = params.tasks.task.status;
        agent.onStatusChangeEmitter.fire(params.tasks.task.status);
      }
    }
  }
  if (params.payload) {
    if (params.payload.ranges) {
      agent.ranges = params.payload.ranges;
    }
  }
  const editors = vscode.window.visibleTextEditors.filter(
    (e) => e.document.uri.toString() == agent?.textDocument?.uri?.toString()
  );
  for (const editor of editors) {
    // [todo] check editor is visible
    const version = editor.document.version;
    if (params.payload) {
      if (params.payload == "accepted" || params.payload == "rejected") {
        agent.status = params.payload;
        agent.onStatusChangeEmitter.fire(params.payload);
        editor.setDecorations(GREEN, []);
        agent.onStatusChangeEmitter.fire(params.payload);
        console.log("SET DECORATIONS TO NONE");
      }
    }
    if (params.payload) {
      if (params.payload.ranges) {
        editor.setDecorations(
          GREEN,
          params.payload.ranges.map(
            (r: { start: { line: number; character: number; }; end: { line: number; character: number; }; }) =>
              new vscode.Range(
                r.start.line,
                r.start.character,
                r.end.line,
                r.end.character
              )
          )
        );
      }
    }
  }
};

export class AgentStateLens extends vscode.CodeLens {
  id: string;
  constructor(range: vscode.Range, agent: any, command?: vscode.Command) {
    super(range, command);
    this.id = agent.id;
  }
}

interface ModelConfig {
  chatModel: string;
  completionsModel: string;
  /** The API key for OpenAI, you can also set OPENAI_API_KEY. */
  openai_api_key?: string;
}

type AgentType = "chat" | "code-completion";
export type AgentIdentifier = string;



export class MorphLanguageClient
  implements vscode.CodeLensProvider<AgentStateLens>
{
  client: LanguageClient | undefined = undefined;
  red: vscode.TextEditorDecorationType;
  green: vscode.TextEditorDecorationType;
  context: vscode.ExtensionContext;
  changeLensEmitter: vscode.EventEmitter<void>;
  onDidChangeCodeLenses: vscode.Event<void>;
  agents: { [id: string]: Agent } = {};
  private webviewState = new Store<WebviewState>(DEFAULT_STATE)
  // agentStates = new Map<AgentIdentifier, any>()

  constructor(context: vscode.ExtensionContext) {
    this.red = { key: "TEMP_VALUE", dispose: () => { } };
    this.green = { key: "TEMP_VALUE", dispose: () => { } };
    this.context = context;
    this.webviewState.subscribe(state => {
      chatProvider.stateUpdate(state);
      logProvider.stateUpdate(state);
    })

    this.create_client().then(() => {
      this.context.subscriptions.push(
        vscode.commands.registerCommand("extension.listAgents", async () => {
          if (client) {
            return await this.list_agents();
          }
        }),
        vscode.commands.registerCommand("rift.cancel", (id: string) =>
          this.client?.sendNotification("morph/cancel", { id })
        ),
        vscode.commands.registerCommand("rift.accept", (id: string) =>
          this.client?.sendNotification("morph/accept", { id })
        ),
        vscode.commands.registerCommand("rift.reject", (id: string) =>
          this.client?.sendNotification("morph/reject", { id })
        ),
        vscode.workspace.onDidChangeConfiguration(
          this.on_config_change.bind(this)
        )
      );

      console.log("runAgent ran");
      const editor = vscode.window.activeTextEditor;
      if (!editor) throw new Error("No active text editor found")
      let textDocument = { uri: editor.document.uri.toString(), version: 0 };
      let position = editor.selection.active;
      const params: ChatAgentParams = {
        agent_type: "rift_chat",
        agent_params: { position, textDocument },
      }
      this.run(params)
      this.refreshWebviewAgents()
    });

    this.changeLensEmitter = new vscode.EventEmitter<void>();
    this.onDidChangeCodeLenses = this.changeLensEmitter.event;
  }

  public getWebviewState() {
    return this.webviewState.value
  }

  // TODO: needs to be modified to account for whether or not an agent has an active cursor in the document whatsoever
  public provideCodeLenses(
    document: vscode.TextDocument,
    token: vscode.CancellationToken
  ): AgentStateLens[] {
    // this returns all of the lenses for the document.
    let items: AgentStateLens[] = [];
    console.log("AGENTS: ", this.agents);

    for (const [id, agent] of Object.entries(this.agents)) {
      if (agent.agent_type != "code_completion") {
        continue;
      }

      if (agent?.textDocument?.uri?.toString() == document.uri.toString()) {
        const line = agent?.position.line;
        const linetext = document.lineAt(line);

        //####### HARDCODED REMOVE THIS #################
        // agent.status = "done";
        //##############################################

        if (agent.status === "running") {
          const running = new AgentStateLens(linetext.range, agent, {
            title: "running",
            command: "rift.cancel",
            tooltip: "click to stop this agent",
            arguments: [agent.id],
          });
          items.push(running);
        } else if (agent.status === "done" || agent.status === "error") {
          const accept = new AgentStateLens(linetext.range, agent, {
            title: "Accept ✅ ",
            command: "rift.accept",
            tooltip: "Accept the edits below",
            arguments: [agent.id],
          });
          const reject = new AgentStateLens(linetext.range, agent, {
            title: " Reject ❌",
            command: "rift.reject",
            tooltip: "Reject the edits below and restore the original text",
            arguments: [agent.id],
          });
          items.push(accept, reject);
        }
      }
    }
    return items;
  }


  public resolveCodeLens(
    codeLens: AgentStateLens,
    token: vscode.CancellationToken
  ) {
    // you use this to resolve the commands for the code lens if
    // it would be too slow to compute the commands for the entire document.
    return null;
  }

  is_running() {
    return this.client && this.client.state == State.Running;
  }

  private async list_agents() {
    if (!this.client) throw new Error();
    const result: AgentRegistryItem[] = await this.client.sendRequest(
      "morph/listAgents",
      {}
    );
    return result;
  }

  public refreshWebviewState() {
    chatProvider.stateUpdate(this.webviewState.value);
    logProvider.stateUpdate(this.webviewState.value);
  }

  public async refreshWebviewAgents() {
    console.log('refreshing webview agents')
    const availableAgents = await this.list_agents()
    this.webviewState.update(state => ({ ...state, availableAgents }))
  }

  async create_client() {
    if (this.client && this.client.state != State.Stopped) {
      console.log(
        `client already exists and is in state ${this.client.state} `
      );
      return;
    }
    const port = DEFAULT_PORT;
    let serverOptions: ServerOptions;
    while (!(await tcpPortUsed.check(port))) {
      console.log("waiting for server to come online");
      try {
        await tcpPortUsed.waitUntilUsed(port, 500, 1000000);
      } catch (e) {
        console.error(e);
      }
    }
    console.log(`server detected on port ${port} `);
    serverOptions = tcpServerOptions(this.context, port);
    const clientOptions: LanguageClientOptions = {
      documentSelector: [{ language: "*" }],
    };
    this.client = new LanguageClient(
      "morph-server",
      "Morph Server",
      serverOptions,
      clientOptions
    );
    this.client.onDidChangeState(async (e) => {
      console.log(`client state changed: ${e.oldState} ▸ ${e.newState} `);
      if (e.newState === State.Stopped) {
        console.log("morph server stopped, restarting...");
        await this.client?.dispose();
        console.log("morph server disposed");
        await this.create_client();
      }
    });
    await this.client.start();
    console.log("rift-engine started");

  }

  async on_config_change(_args: any) {
    if (!this.client) throw new Error('no client')
    const x = await this.client.sendRequest(
      "workspace/didChangeConfiguration",
      {}
    );
  }

  async notify_focus(tdpp: TextDocumentPositionParams | { symbol: string }) {
    // [todo] unused
    console.log(tdpp);
    await this.client?.sendNotification("morph/focus", tdpp);
  }

  async hello_world() {
    const result = await this.client?.sendRequest("hello_world");
    return result;
  }

  morphNotifyChatCallback: (progress: ChatAgentProgress) => any =
    async function (progress) {
      throw new Error("no callback set");
    };


  // deprecated
  // async run_chat(
  //   params: RunChatParams,
  //   callback: (progress: ChatAgentProgress) => any
  // ) {
  //   console.log("run chat");
  //   if (!this.client) throw new Error();
  //   this.morphNotifyChatCallback = callback;
  //   this.client.onNotification(
  //     "morph/chat_progress",
  //     this.morphNotifyChatCallback.bind(this)
  //   );

  //   const result = await this.client.sendRequest("morph/run_chat", params);
  //   // note this returns fast and then the updates are sent via notifications
  //   return "starting...";
  // }

  async run(params: RunAgentParams) {
    if (!this.client) throw new Error();
    const result: RunAgentResult = await this.client.sendRequest(
      "morph/run",
      params
    );
    console.log("run agent result");
    console.log(result);
    const agent_id = result.id;
    const agent_type = params.agent_type;

    const editor = vscode.window.activeTextEditor;
    if (!editor) throw new Error("No active text editor");
    // get the uri and position of the current cursor
    const doc = editor.document;
    const textDocument = { uri: doc.uri.toString(), version: 0 };
    const position = editor.selection.active;

    const agent = new Agent(
      this,
      result.id,
      agent_type,
      position,
      textDocument,
      params
    );

    this.webviewState.update((state) => ({
      ...state,
      selectedAgentId: (agent.agent_type !== 'code_completion') ? agent_id : state.selectedAgentId, //TODO handle for general cases
      agents: {
        ...state.agents,
        [agent_id]: new WebviewAgent(agent_type),
      }
    }
    ))


    agent.onStatusChange((e) => this.changeLensEmitter.fire());
    this.agents[result.id] = agent;
    this.changeLensEmitter.fire();

    // this.agentStates.set(agentIdentifier, { agent_id: agent_id, agent_type: agent_type, status: "running", ranges: [], tasks: [], emitter: new vscode.EventEmitter<AgentStatus>, params: params.agent_params })
    this.client.onRequest(
      `morph/${agent_type}_${agent_id}_request_input`,
      agent.handleInputRequest.bind(agent)
    );
    this.client.onRequest(
      `morph/${agent_type}_${agent_id}_request_chat`,
      agent.handleChatRequest.bind(agent)
    );
    // note(jesse): for the chat agent, the request_chat callback should register another callback for handling user responses --- it should unpack the future identifier from the request_chat_request and re-pass it to the language server
    this.client.onNotification(
      `morph/${agent_type}_${agent_id}_send_update`,
      agent.handleUpdate.bind(agent)
    ); // this should post a message to the rift logs webview if `tasks` have been updated
    this.client.onNotification(
      `morph/${agent_type}_${agent_id}_send_progress`,
      agent.handleProgress.bind(agent)
    ); // this should post a message to the rift logs webview if `tasks` have been updated
    // actually, i wonder if the server should just be generally responsible for sending notifications to the client about active tasks
    this.client.onNotification(
      `morph/${agent_type}_${agent_id}_send_result`,
      agent.handleResult.bind(agent)
    ); // this should be custom

  }

  async cancel(params: AgentIdParams) {
    if (!this.client) throw new Error();
    let response = await this.client.sendRequest("morph/cancel", params);
    return response;
  }

  async delete(params: AgentIdParams) {
    if (!this.client) throw new Error();
    let response = await this.client.sendRequest("morph/cancel", params);
    this.webviewState.update((state) => {
      const updatedAgents = { ...state.agents }
      updatedAgents[params.id]
      return {
        ...state,
        agents: {
          ...state.agents,
          [params.id]: {
            ...state.agents[params.id],
            isDeleted: true,
          },
        }
      }
    })


    return response;
  }

  async restart_agent(agentId: string) {
    if (!this.client) throw new Error();
    if (!(agentId in this.webviewState.value.agents)) throw new Error(`tried to restart agent ${agentId} but couldn't find it in agents object`)
    const agent_type = this.webviewState.value.agents[agentId].type
    let result: RunAgentResult = await this.client.sendRequest("morph/restart_agent", {id: agentId});
    this.webviewState.update((state) => ({
      ...state,
      agents: {
        ...state.agents,
        [agentId]: new WebviewAgent(agent_type),
      }
    }
    ))
  }

  public restartActiveAgent() {
    this.restart_agent(this.webviewState.value.selectedAgentId)
  }


  sendChatHistoryChange(agentId: string, newChatHistory: ChatMessage[]) {
    // const currentChatHistory = this.webviewState.value.agents[agentId].chatHistory
    console.log(`updating chat history for ${agentId}`)

    // if (newChatHistory.length > 1) {
    //   throw new Error("No previous messages on client for this ID, but server is giving multiple chat messages.")
    // }
    this.webviewState.update(state => {
      if (!(agentId in state.agents)) throw new Error('changing chatHistory for nonexistent agent')
      return ({
        ...state,
        agents: {
          ...state.agents,
          [agentId]: {
            ...state.agents[agentId],
            chatHistory: [...newChatHistory],
          },
        },
      })
    });

  }

  sendProgressChange(params: AgentProgress) {
    console.log('progress')
    console.log(params)
    let agentId = params.agent_id;

    if (!(agentId in this.webviewState.value.agents)) throw new Error('progress for nonexistent agent')

    const response = params.payload?.response;

    if (response) this.webviewState.update(state => ({ ...state, agents: { ...state.agents, [agentId]: { ...state.agents[agentId], streamingText: response, isStreaming: true } } }))

    this.webviewState.update(state => ({
      ...state,
      agents: {
        ...state.agents,
        [agentId]: {
          ...state.agents[agentId],
          type: params.agent_type,
          tasks: params.tasks,
        },
      },
    }));



    if (params.payload?.done_streaming) {
      if (!response) throw new Error(" done streaming but no response?");
      this.webviewState.update((prevState) => {
        return {
          ...prevState,
          agents: {
            ...prevState.agents,
            [agentId]: {
              ...prevState.agents[agentId],
              agent_id: agentId,
              agent_type: params.agent_type,
              isStreaming: false,
              streamingText: '',
              tasks: params.tasks,
              chatHistory: [
                ...prevState.agents[agentId].chatHistory ?? [],
                { role: "assistant", content: response },
              ],
            },
          },
        };
      });

    }
  }

  sendHasNotificationChange(agentId: string, hasNotification: boolean) {
    if (!(agentId in this.webviewState.value.agents)) throw new Error('cant update nonexistent agent')
    this.webviewState.update(state => ({
      ...state,
      agents: {
        ...state.agents,
        [agentId]: {
          ...state.agents[agentId],
          hasNotification: (agentId == state.selectedAgentId) ? false : hasNotification //this ternary operatory will make sure we don't set currently selected agents as having notifications
        }
      }
    }))
  }

  sendSelectedAgentChange(agentId: string) {

    this.webviewState.update(state => {
      if (!(agentId in state.agents)) throw new Error(`tried to change selectedAgentId to an unavailable agent. tried to change to ${agentId} but available agents are: ${Object.keys(state.agents)}`)

      return ({ ...state, selectedAgentId: agentId })
    })
  }

  //TODO:
  // async delete(params: AgentIdParams) {
  //     if (!this.client) throw new Error()
  //     let response = await this.client.sendRequest('morph/delete', {})
  //     return response;
  // }


  dispose() {
    this.client?.dispose();
  }


}


class Agent {
  status: AgentStatus;
  green: vscode.TextEditorDecorationType;
  ranges: vscode.Range[] = [];
  onStatusChangeEmitter: vscode.EventEmitter<AgentStatus>;
  onStatusChange: vscode.Event<AgentStatus>;
  morph_language_client: MorphLanguageClient

  constructor(
    morph_language_client: MorphLanguageClient,
    public readonly id: string,
    public readonly agent_type: string,
    public readonly position: vscode.Position,
    public textDocument: TextDocumentIdentifier,
    public params: any
  ) {
    this.morph_language_client = morph_language_client;
    this.id = id;
    this.status = "running";
    this.agent_type = agent_type;
    this.position = position;
    this.textDocument = textDocument;
    this.green = vscode.window.createTextEditorDecorationType({
      backgroundColor: "rgba(0,255,0,0.1)",
    });
    this.onStatusChangeEmitter = new vscode.EventEmitter<AgentStatus>();
    this.onStatusChange = this.onStatusChangeEmitter.event;
  }

  async handleInputRequest(params: AgentInputRequest) {
    /*
            const input_request = event.data.data as AgentInputRequest;
        // let agentId = input_request.agent_id;
        // let status = input_request.tasks.task.status;
        state.update((prevState) => ({
          ...prevState,
          agents: {
            ...prevState.agents,
            [input_request.id]: {
              ...prevState.agents[input_request.id],
              inputRequest: {
                msg: input_request.msg,
                place_holder: input_request.place_holder,
              },
            },
          },
        }));*/
    // case "input_request": {
    //     const input_request = event.data.data as AgentInputRequest;
    //     if ($state.selectedAgentId == input_request.id) {
    //         state.update((state) => ({
    //             ...state,
    //             agents: {
    //                 ...state.agents,
    //                 [input_request.id!]: {
    //                     ...state.agents[input_request.id!],
    //                     hasInputNotification: false,
    //                 },
    //             },
    //         }));
    //     } else if ($state.selectedAgentId != input_request.id) {
    //         state.update((state) => ({
    //             ...state,
    //             agents: {
    //                 ...state.agents,
    //                 [input_request.id!]: {
    //                     ...state.agents[input_request.id!],
    //                     hasInputNotification: true,
    //                 },
    //             },
    //         }));
    //     }

    //     break;
    // }


    // logProvider._view?.webview.postMessage({
    //   type: "chat_request",
    //   data: { ...params, id: this.id },
    // });


    /* this logic was the one I pulled from logswebview that was implemented -- Brent
                const chat_request = event.data.data as AgentChatRequest;
                if ($state.selectedAgentId == chat_request.id) {
                    state.update((state) => ({
                        ...state,
                        agents: {
                            ...state.agents,
                            [chat_request.id!]: {
                                ...state.agents[chat_request.id!],
                                hasNotification: false,
                            },
                        },
                    }));
                } else if ($state.selectedAgentId != chat_request.id) {
                    state.update((state) => ({
                        ...state,
                        agents: {
                            ...state.agents,
                            [chat_request.id!]: {
                                ...state.agents[chat_request.id!],
                                hasNotification: true,
                            },
                        },
                    }));
                }
    */
    if (!(this.id in this.morph_language_client.agents)) throw Error("Agent does not exist")

    let response = await vscode.window.showInputBox({
      ignoreFocusOut: true,
      placeHolder: params.place_holder,
      prompt: params.msg,
    });
    return { response: response };
  }

  async handleChatRequest(params: AgentChatRequest) {
    if (!(this.id in this.morph_language_client.agents)) throw Error("Agent does not exist")
    console.log("handleChatRequest");
    console.log(params);
    console.log("agentType:", this.agent_type);
    // if(!params.id) throw new Error('no params')

    this.morph_language_client.sendChatHistoryChange(this.id, params.messages)
    this.morph_language_client.sendHasNotificationChange(this.id, true)

    const agentType = this.agent_type;
    const agentId = this.id

    console.log("agentId:", this.id);

    // return "BLAH BLAH"
    async function getUserInput() {
      console.log("getUserInput");

      return new Promise((res, rej) => {
        console.log("subscribing to changes");
        PubSub.sub(`${agentType}_${agentId}_chat_request`, (message) => {
          console.log("resolving promise");
          res(message);
        });
      });
    }

    let chatRequest = await getUserInput();
    console.log("received user input and returning to server");
    console.log(chatRequest);
    return chatRequest;
  }
  async handleUpdate(params: AgentUpdate) {
    if (!(this.id in this.morph_language_client.agents)) throw Error("Agent does not exist")
    console.log("handleUpdate");
    console.log(params);

    vscode.window.showInformationMessage(params.msg);
  }
  async handleProgress(params: AgentProgress) {
    if (!(this.id in this.morph_language_client.agents)) throw Error("Agent does not exist")
    this.morph_language_client.sendProgressChange(params)

    if (this.agent_type === "code_completion") {
      code_completion_send_progress(params, this);
    }
  }
  async handleResult(params: AgentResult) {
    if (!(this.id in this.morph_language_client.agents)) throw Error("Agent does not exist")
    console.log("handleResult");
    console.log(params);

    throw new Error("no logic written for handle result yet")
  }
}

// class ChatAgent extends Agent {
//   status: AgentStatus;
//   green: vscode.TextEditorDecorationType;
//   ranges: vscode.Range[] = [];
//   onStatusChangeEmitter: vscode.EventEmitter<AgentStatus>;
//   onStatusChange: vscode.Event<AgentStatus>;
//   morph_language_client: MorphLanguageClient

//   constructor(
//     morph_language_client: MorphLanguageClient,
//     public readonly id: string,
//     public readonly agent_type: string,
//     public readonly position: vscode.Position,
//     public textDocument: TextDocumentIdentifier,
//     public params: any
//   ) {
//     this.morph_language_client = morph_language_client;
//     this.id = id;
//     this.status = "running";
//     this.agent_type = agent_type;
//     this.position = position;
//     this.textDocument = textDocument;
//     this.green = vscode.window.createTextEditorDecorationType({
//       backgroundColor: "rgba(0,255,0,0.1)",
//     });
//     this.onStatusChangeEmitter = new vscode.EventEmitter<AgentStatus>();
//     this.onStatusChange = this.onStatusChangeEmitter.event;
//   }
// }