import * as vscode from "vscode";
// import { MorphLanguageClient, RunChatParams } from "../client";
import * as client from "../client"
import { getNonce } from "../getNonce";
import { ChatAgentProgress } from "../types";

// Provides a webview view that allows users to chat and interact with the extension.
export class ChatProvider implements vscode.WebviewViewProvider {
    _view?: vscode.WebviewView;
    _doc?: vscode.TextDocument;

    // Creates a new instance of `ChatProvider`.
    //  _extensionUri: The URI of the extension.
    //  morph_language_client: The MorphLanguageClient instance for communication with the server.
    constructor(private readonly _extensionUri: vscode.Uri, public morph_language_client: client.MorphLanguageClient) {
    }

    // Posts a message to the webview view.
    //  endpoint: The endpoint to send the message to.
    //  message: The message to send.
    //  Throws an error if the view is not available.
    public postMessage(endpoint: string, message: any) {
        if (!this._view) {
            throw new Error('No view available');
        } else {
            this._view.webview.postMessage({ type: endpoint, data: message });
        }
    }

    public resolveWebviewView(
        webviewView: vscode.WebviewView,
        context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ) {
        this._view = webviewView;
        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [
                this._extensionUri
            ]
        };
        webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);

        // Handles messages received from the webview
        webviewView.webview.onDidReceiveMessage(async (params: any) => {
            if (!this._view) throw new Error('no view')
            switch (params.type) {
                // Handle 'copyText' message
                case "copyText":
                    console.log('recieved copy in webview')
                    vscode.env.clipboard.writeText(params.content)
                    vscode.window.showInformationMessage('Text copied to clipboard!')
                    break;

                // Handle 'getAgents' message
                case "listAgents":
                    const agents: client.AgentRegistryItem[] = await this.morph_language_client.list_agents();
                    console.log("Getting list of available agents");
                    this._view.webview.postMessage({
                        type: 'agents',
                        data: agents
                    });
                    break;

                // Handle 'getAgents' message
                case "runAgent":
                    console.log("TODO");

                    // const runAgentParams: client.RunChatParams = { agent_type: params.agent_type, agent_params: params.agent_params };
                    // const agents: client.AgentRegistryItem[] = await this.morph_language_client.list_agents();
                    // console.log("Getting list of available agents")
                    // this._view.webview.postMessage({
                    //         type: 'agents',
                    //         data: agents
                    // });
                    break;

                // Handle 'chatMessage' message
                case 'chatMessage':
                    const editor = vscode.window.activeTextEditor;
                    let runChatParams: any = { message: params.message, messages: params.messages }
                    if (!editor) {
                        console.warn('No active text editor found');
                    } else {
                        // Get the uri and position of the current cursor
                        const doc = editor.document;
                        const position = editor.selection.active;
                        const textDocument = { uri: doc.uri.toString(), version: 0 }
                        runChatParams = { message: params.message, messages: params.messages, position, textDocument }
                    }
                    if (!params.message || !params.messages) throw new Error()
                    this.morph_language_client.run_chat(runChatParams, (progress) => {
                        console.log(progress)
                        if (!this._view) throw new Error('no view')
                        if (progress.done) console.log('WEBVIEW DONE RECEIVING / POSTING')
                        this._view.webview.postMessage({ type: 'progress', data: progress });
                    })
                    break;

                default:
                    console.log('no case match')
            }

        });
    }

    public revive(panel: vscode.WebviewView) {
        this._view = panel;
    }

    private _getHtmlForWebview(webview: vscode.Webview) {
        const scriptUri = webview.asWebviewUri(
            vscode.Uri.joinPath(this._extensionUri, "out", "compiled/Chat.js")
        );

        const cssUri = webview.asWebviewUri(
            vscode.Uri.joinPath(this._extensionUri, "out", "compiled/Chat.css")
        );

        const stylesResetUri = webview.asWebviewUri(
            vscode.Uri.joinPath(this._extensionUri, "media", "reset.css")
        );

        const tailwindUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'media', 'scripts', 'tailwind.min.js'));

        const showdownUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'media', 'scripts', 'showdown.min.js'));

        const microlightUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'media', 'scripts', 'microlight.min.js'));

        // Use a nonce to only allow specific scripts to be run
        const nonce = getNonce();

        return `<!DOCTYPE html>
            <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <!--
                        Use a content security policy to only allow loading images from https or from our extension directory,
                        and only allow scripts that have a specific nonce.
                    -->
                    <meta http-equiv="Content-Security-Policy" content="img-src https: data:; style-src 'unsafe-inline' ${webview.cspSource}; script-src 'nonce-${nonce}';">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <link href="${stylesResetUri}" rel="stylesheet">
                        
                    <script src="${tailwindUri}" nonce="${nonce}"></script>
                    <script src="${showdownUri}" nonce="${nonce}"></script>
                    <script src="${microlightUri}" nonce="${nonce}"></script>
                    <link href="${cssUri}" rel="stylesheet">
                    <script nonce="${nonce}">
                        const vscode = acquireVsCodeApi();
                    </script>
                </head>
                <body class="p-0">
                </body>
                <script nonce="${nonce}" src="${scriptUri}"></script>
            </html>`;
    }
}
