import * as path from 'path';
import type { workspace, ExtensionContext } from 'vscode'
import * as vscode from 'vscode'
import { ChildProcessWithoutNullStreams, spawn } from 'child_process'
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
import * as net from 'net'
import { join } from 'path';
import * as tcpPortUsed from 'tcp-port-used'
import { chatProvider, logProvider, morph_language_client } from './extension';
import PubSub from './lib/PubSub';


let client: LanguageClient //LanguageClient

const DEFAULT_PORT = 7797

// ref: https://stackoverflow.com/questions/40284523/connect-external-language-server-to-vscode-extension

// https://nodejs.org/api/child_process.html#child_processspawncommand-args-options

/** Creates the ServerOptions for a system in the case that a language server is already running on the given port. */
function tcpServerOptions(context: ExtensionContext, port = DEFAULT_PORT): ServerOptions {
    let socket = net.connect({
        port: port, host: "127.0.0.1"
    })
    const si: StreamInfo = {
        reader: socket, writer: socket
    }
    return () => {
        return Promise.resolve(si)
    }
}

/** Creates the server options for spinning up our own server.*/
function createServerOptions(context: vscode.ExtensionContext, port = DEFAULT_PORT): ServerOptions {
    let cwd = vscode.workspace.workspaceFolders![0].uri.path
    // [todo]: we will supply different bundles for the 3 main platforms; windows, linux, osx.
    // there needs to be a decision point here where we decide which platform we are on and
    // then choose the appropriate bundle.
    let command = join(context.extensionPath, 'resources', 'lspai')
    let args: string[] = []
    args = [...args, '--port', port.toString()]
    let e: Executable = {
        command,
        args,
        transport: { kind: TransportKind.socket, port },
        options: { cwd },
    }
    return {
        run: e, debug: e
    }
}

interface RunCodeHelperParams {
    instructionPrompt: string
    position: vscode.Position
    textDocument: TextDocumentIdentifier
}

export interface RunAgentParams {
    agent_type: string
    agent_params: any
}

// interface RunAgentResult {
//     id: number
//     agentId: string | null
// }

export interface RunChatParams {
    message: string
    messages: { // does not include latest message
        role: string,
        content: string
    }[],
    // position: vscode.Position,
    // textDocument: TextDocumentIdentifier,
}

export interface AgentRegistryItem {
    agent_type: string,
    agent_description: string,
    display_name: string,
    agent_icon: string | null,
}


interface RunAgentResult {
    id: string
}

interface RunAgentSyncResult {
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


export type ChatAgentProgress = AgentProgress<{ response?: string, done_streaming?: boolean } | undefined>


export interface AgentProgress<T = any> {
    agent_id: string,
    agent_type: string,
    tasks: Tasks,
    payload: T,
}

export interface AgentId {
    id: string
}

export type ChatMessage = {
    role: "user" | "assistant"
    content: string
    name?: null | string | undefined
};

export interface AgentChatRequest {
    messages: ChatMessage[]
    id: string
}

export interface AgentInputRequest {
    id: string
    msg: string
    place_holder: string
}

export interface AgentInputResponse {
    response: string
}

export interface AgentUpdate {
    msg: string
}
export type AgentResult = {
    id: string,
    type: string
} //is just an ID rn



const code_completion_send_progress_callback = async (params: any) => {
    const green = vscode.window.createTextEditorDecorationType({ backgroundColor: 'rgba(0,255,0,0.1)' })
    const key: string = `code_completion_${params.agent_id}`
    if (params.tasks) {
        logProvider.postMessage("tasks", { agent_id: params.agent_id, ...params.tasks })
        if (params.tasks.task.status) {
            if (morph_language_client.agentStates.get(key).status !== params.tasks.task.status) {
                morph_language_client.agentStates.get(key).status = params.tasks.task.status
                morph_language_client.agentStates.get(key).emitter.fire(params.tasks.task.status)
            }
        }
    }
    if (params.payload) {
        if (params.payload.ranges) {
            morph_language_client.agentStates.get(key).ranges = params.payload.ranges
        }
    }
    const editors = vscode.window.visibleTextEditors.filter(e => e.document.uri.toString() == morph_language_client.agentStates.get(key).params.textDocument.uri.toString())
    for (const editor of editors) {
        // [todo] check editor is visible
        const version = editor.document.version
        if (params.tasks) {
            if (params.tasks.task.status == 'accepted' || params.tasks.task.status == 'rejected') {
                editor.setDecorations(green, [])
                continue
            }
        }
        if (params.payload) {
            if (params.payload.ranges) {
                editor.setDecorations(green, params.payload.ranges.map(r => new vscode.Range(r.start.line, r.start.character, r.end.line, r.end.character)))
            }
        }
    }
}

class Agent {
    status: AgentStatus;
    green: vscode.TextEditorDecorationType;
    ranges: vscode.Range[] = []
    onStatusChangeEmitter: vscode.EventEmitter<AgentStatus>
    onStatusChange: vscode.Event<AgentStatus>
    constructor(public readonly id: string, public readonly agent_type: string, public readonly startPosition: vscode.Position, public textDocument: TextDocumentIdentifier) {
        this.id = id;
        this.status = 'running';
        this.agent_type = agent_type;
        this.green = vscode.window.createTextEditorDecorationType({ backgroundColor: 'rgba(0,255,0,0.1)' })
        this.onStatusChangeEmitter = new vscode.EventEmitter<AgentStatus>()
        this.onStatusChange = this.onStatusChangeEmitter.event

    }
    async handleInputRequest(params: AgentInputRequest) {
        let response = await vscode.window.showInputBox({
            ignoreFocusOut: true,
            placeHolder: params.place_holder,
            prompt: params.msg,
        });
        return { response: response }
    }

    async handleChatRequest(params: AgentChatRequest) {
        console.log("handleChatRequest");
        console.log(params)
        chatProvider._view?.webview.postMessage({ type: 'chat_request', data: { ...params, id: this.id } });
        logProvider._view?.webview.postMessage({ type: 'chat_request', data: { ...params, id: this.id } });

        let agentType = this.agent_type
        let agentId = this.id

        console.log('agentType:', agentType)
        console.log('agentId:', agentId)

        // return "BLAH BLAH"
        async function getUserInput() {
            console.log('getUserInput')
            console.log('agentType:', agentType)
            console.log('agentId:', agentId)
            return new Promise((res, rej) => {
                console.log('subscribing to changes')
                PubSub.sub(`${agentType}_${agentId}_chat_request`, (message) => {
                    console.log('resolving promise')
                    res(message)
                })
            })
        }

        let chatRequest = await getUserInput();
        console.log('received user input and returning to server')
        console.log(chatRequest)
        return chatRequest;
    }
    async handleUpdate(params: AgentUpdate) {
        console.log("handleUpdate")
        console.log(params)
        // //chatProvider._view?.webview.postMessage({ type: 'update', data: params });
        // logProvider._view?.webview.postMessage({ type: 'update', data: params });
        vscode.window.showInformationMessage(params.msg);
    }
    async handleProgress(params: AgentProgress) {
        console.log("handleProgress")
        console.log(params)
        chatProvider._view?.webview.postMessage({ type: 'progress', data: params });
        logProvider._view?.webview.postMessage({ type: 'progress', data: params });


        if (this.agent_type === "code_completion") {
            code_completion_send_progress_callback(params);
        }
    }
    async handleResult(params: AgentResult) {
        console.log("handleResult")
        console.log(params)
        chatProvider._view?.webview.postMessage({ type: 'result', data: params });
        logProvider._view?.webview.postMessage({ type: 'result', data: params });
    }
}





export class AgentStateLens extends vscode.CodeLens {
    id: number
    constructor(range: vscode.Range, agentState: any, command?: vscode.Command) {
        super(range, command)
        this.id = agentState.agent_id
    }
}

interface ModelConfig {
    chatModel: string
    completionsModel: string
    /** The API key for OpenAI, you can also set OPENAI_API_KEY. */
    openai_api_key?: string
}

type AgentType = "chat" | "code-completion"
export type AgentIdentifier = string

export class MorphLanguageClient implements vscode.CodeLensProvider<AgentStateLens> {
    client: LanguageClient | undefined = undefined
    red: vscode.TextEditorDecorationType
    green: vscode.TextEditorDecorationType
    context: vscode.ExtensionContext
    changeLensEmitter: vscode.EventEmitter<void>
    onDidChangeCodeLenses: vscode.Event<void>
    agents = new Map<AgentIdentifier, Agent>()
    agentStates = new Map<AgentIdentifier, any>()

    constructor(context: vscode.ExtensionContext) {
        this.red = { key: "TEMP_VALUE", dispose: () => { } }
        this.green = { key: "TEMP_VALUE", dispose: () => { } }
        this.context = context
        this.create_client().then(() => {
            this.context.subscriptions.push(
                vscode.commands.registerCommand('extension.listAgents', async () => {
                    if (client) {
                        return await this.list_agents();
                    }
                }),
                vscode.commands.registerCommand('rift.cancel', (id: number) => this.client?.sendNotification('morph/cancel', { id })),
                vscode.commands.registerCommand('rift.accept', (id: number) => this.client?.sendNotification('morph/accept', { id })),
                vscode.commands.registerCommand('rift.reject', (id: number) => this.client?.sendNotification('morph/reject', { id })),
                vscode.workspace.onDidChangeConfiguration(this.on_config_change.bind(this)),
            )
        })


        this.changeLensEmitter = new vscode.EventEmitter<void>()
        this.onDidChangeCodeLenses = this.changeLensEmitter.event
    }

    // TODO: needs to be modified to account for whether or not an agent has an active cursor in the document whatsoever
    public provideCodeLenses(document: vscode.TextDocument, token: vscode.CancellationToken): AgentStateLens[] {
        // this returns all of the lenses for the document.
        const items: AgentStateLens[] = []
        for (const agentState of this.agentStates.values()) {
            if (agentState.agent_type == "code_completion" && agentState.params.textDocument.uri.toString() == document.uri.toString()) {
                const line = agentState.params.position.line
                const linetext = document.lineAt(line)
                if (agentState.status === 'running') {
                    const running = new AgentStateLens(linetext.range, agentState, {
                        title: 'cancel',
                        command: 'rift.cancel',
                        tooltip: 'click to stop this agent',
                        arguments: [agentState.agent_id],
                    })
                    items.push(running)
                }
                else if (agentState.status === 'done' || agentState.status === 'error') {
                    const accept = new AgentStateLens(linetext.range, agentState, {
                        title: 'Accept ✅ ',
                        command: 'rift.accept',
                        tooltip: 'Accept the edits below',
                        arguments: [agentState.agent_id],
                    })
                    const reject = new AgentStateLens(linetext.range, agentState, {
                        title: ' Reject ❌',
                        command: 'rift.reject',
                        tooltip: 'Reject the edits below and restore the original text',
                        arguments: [agentState.agent_id]
                    })
                    items.push(accept, reject)
                }
            }
        }
        return items
    }

    // // TODO: needs to be modified to account for whether or not an agent has an active cursor in the document whatsoever
    // public provideCodeLenses(document: vscode.TextDocument, token: vscode.CancellationToken): AgentLens[] {
    //     // this returns all of the lenses for the document.
    //     const items: AgentLens[] = []
    //     for (const agent of this.agents.values()) {
    //         if (agent.textDocument.uri === document.uri.toString()) {
    //             const line = agent.startPosition.line
    //             const linetext = document.lineAt(line)
    //             if (agent.status === 'running') {
    //                 const running = new AgentLens(linetext.range, agent, {
    //                     title: 'running',
    //                     command: 'rift.cancel',
    //                     tooltip: 'click to stop this agent',
    //                     arguments: [agent.id],
    //                 })
    //                 items.push(running)
    //             }
    //             else if (agent.status === 'done' || agent.status === 'error') {
    //                 const accept = new AgentLens(linetext.range, agent, {
    //                     title: 'Accept ✅ ',
    //                     command: 'rift.accept',
    //                     tooltip: 'Accept the edits below',
    //                     arguments: [agent.id],
    //                 })
    //                 const reject = new AgentLens(linetext.range, agent, {
    //                     title: ' Reject ❌',
    //                     command: 'rift.reject',
    //                     tooltip: 'Reject the edits below and restore the original text',
    //                     arguments: [agent.id]
    //                 })
    //                 items.push(accept, reject)
    //             }
    //         }
    //     }
    //     return items
    // }

    public resolveCodeLens(codeLens: AgentStateLens, token: vscode.CancellationToken) {
        // you use this to resolve the commands for the code lens if
        // it would be too slow to compute the commands for the entire document.
        return null
    }

    is_running() {
        return this.client && this.client.state == State.Running
    }

    async list_agents() {
        console.log('get agents client.ts');
        if (!this.client) throw new Error()
        const result: AgentRegistryItem[] = await this.client.sendRequest('morph/listAgents', {})
        console.log(result);
        return result;
    }

    async create_client() {
        if (this.client && this.client.state != State.Stopped) {
            console.log(`client already exists and is in state ${this.client.state} `)
            return
        }
        const port = DEFAULT_PORT
        let serverOptions: ServerOptions
        while (!(await tcpPortUsed.check(port))) {
            console.log('waiting for server to come online')
            try {
                await tcpPortUsed.waitUntilUsed(port, 500, 1000000)
            }
            catch (e) {
                console.error(e)
            }
        }
        console.log(`server detected on port ${port} `)
        serverOptions = tcpServerOptions(this.context, port)
        const clientOptions: LanguageClientOptions = {
            documentSelector: [{ language: '*' }]
        }
        this.client = new LanguageClient(
            'morph-server', 'Morph Server',
            serverOptions, clientOptions,
        )
        this.client.onDidChangeState(async e => {
            console.log(`client state changed: ${e.oldState} ▸ ${e.newState} `)
            if (e.newState === State.Stopped) {
                console.log('morph server stopped, restarting...')
                await this.client?.dispose()
                console.log('morph server disposed')
                await this.create_client()
            }
        })
        await this.client.start()
        console.log('rift-engine started')
    }


    async on_config_change(_args: any) {
        const x = await this.client?.sendRequest('workspace/didChangeConfiguration', {})
    }

    async notify_focus(tdpp: TextDocumentPositionParams | { symbol: string }) {
        // [todo] unused
        console.log(tdpp)
        await this.client?.sendNotification('morph/focus', tdpp)
    }

    async hello_world() {
        const result = await this.client?.sendRequest('hello_world')
        return result
    }

    morphNotifyChatCallback: (progress: ChatAgentProgress) => any = async function (progress) {
        throw new Error('no callback set')
    }

    async run_chat(params: RunChatParams, callback: (progress: ChatAgentProgress) => any) {
        console.log('run chat')
        if (!this.client) throw new Error()
        this.morphNotifyChatCallback = callback
        this.client.onNotification('morph/chat_progress', this.morphNotifyChatCallback.bind(this))

        const result = await this.client.sendRequest('morph/run_chat', params)
        // note this returns fast and then the updates are sent via notifications
        return 'starting...'
    }


    async run(params: RunAgentParams) {
        if (!this.client) throw new Error()
        const result: RunAgentResult = await this.client.sendRequest('morph/run', params);
        console.log('run agent result')
        console.log(result)
        const agent_id = result.id;
        const agent_type = params.agent_type;

        const agent = new Agent(result.id, agent_type, params.agent_params.position, params.agent_params.textDocument)
        agent.onStatusChange(e => this.changeLensEmitter.fire())
        this.agents.set(result.id.toString(), agent)
        this.changeLensEmitter.fire()

        console.log(`running ${agent_type} `)
        const agentIdentifier = `${agent_type}_${agent_id} `
        console.log(`agentIdentifier: ${agentIdentifier} `)
        this.agentStates.set(agentIdentifier, { agent_id: agent_id, agent_type: agent_type, status: "running", ranges: [], tasks: [], emitter: new vscode.EventEmitter<AgentStatus>, params: params.agent_params })
        this.client.onRequest(`morph/${agent_type}_${agent_id}_request_input`, agent.handleInputRequest.bind(agent))
        this.client.onRequest(`morph/${agent_type}_${agent_id}_request_chat`, agent.handleChatRequest.bind(agent))
        // note(jesse): for the chat agent, the request_chat callback should register another callback for handling user responses --- it should unpack the future identifier from the request_chat_request and re-pass it to the language server
        this.client.onNotification(`morph/${agent_type}_${agent_id}_send_update`, agent.handleUpdate.bind(agent)) // this should post a message to the rift logs webview if `tasks` have been updated
        this.client.onNotification(`morph/${agent_type}_${agent_id}_send_progress`, agent.handleProgress.bind(agent)) // this should post a message to the rift logs webview if `tasks` have been updated
        // actually, i wonder if the server should just be generally responsible for sending notifications to the client about active tasks
        this.client.onNotification(`morph/${agent_type}_${agent_id}_send_result`, agent.handleResult.bind(agent)) // this should be custom


        return { id: agent_id, type: agent_type }// return agent_id to the webview
    }

    async cancel(params: AgentId) {
        if (!this.client) throw new Error()
        let response = await this.client.sendRequest('morph/cancel', params);
        return response;
    }

    //TODO:
    // async delete(params: AgentIdParams) {
    //     if (!this.client) throw new Error()
    //     let response = await this.client.sendRequest('morph/delete', {})
    //     return response;
    // }

    // run should spawn an agent
    // run should specify:
    // - agent type
    // - callbacks for request_input, request_chat, send_progress, and send_result

    // async run_chat(params: RunChatParams, callback: (progress: ChatAgentProgress) => any) {
    //     console.log('run chat')
    //     this.morphNotifyChatCallback = callback
    //     this.client.onNotification('morph/chat_progress', this.morphNotifyChatCallback.bind(this))

    //     const result = await this.client.sendRequest('morph/run_chat', params)
    //     // note this returns fast and then the updates are sent via notifications
    //     return 'starting...'
    // }

    dispose() {
        this.client?.dispose()
    }

    // async provideInlineCompletionItems(doc: vscode.TextDocument, position: vscode.Position, context: vscode.InlineCompletionContext, token: vscode.CancellationToken) {
    //     const params: RunCodeHelperParams = { instructionPrompt: "complete the code", position: position, textDocument: TextDocumentIdentifier.create(doc.uri.toString()) };
    //     const snippet = new vscode.SnippetString(await this.run_agent_sync(params));
    //     // return new vscode.InlineCompletionList([{insertText: snippet}]);
    //     return snippet;
    // }
}
