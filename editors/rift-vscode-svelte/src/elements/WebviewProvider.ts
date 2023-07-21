import * as vscode from "vscode";
// import { MorphLanguageClient, RunChatParams } from "../client";
// import * as client from '../client'
import {getNonce} from "../getNonce";
import PubSub from "../lib/PubSub";
import type {MorphLanguageClient, RunAgentParams,} from "../client";
import {WebviewState} from "../types";

// Provides a webview view that allows users to chat and interact with the extension.
export class WebviewProvider implements vscode.WebviewViewProvider {
  _view?: vscode.WebviewView;
  _doc?: vscode.TextDocument;

  // Creates a new instance of `ChatProvider`.
  //  _extensionUri: The URI of the extension.
  //  morph_language_client: The MorphLanguageClient instance for communication with the server.
  constructor(
    public name: "Chat" | "Logs",
    private readonly _extensionUri: vscode.Uri,
    public morph_language_client: MorphLanguageClient
  ) {}

  // Posts a message to the webview view.
  //  endpoint: The endpoint to send the message to.
  //  message: The message to send.
  //  Throws an error if the view is not available.
  // notice: the only things being posted to the webviews are state objects, so this will be a private function
  private postMessage(endpoint: string, message: any) {
    if (!this._view) {
      throw new Error("No view available");
    } else {
      this._view.webview.postMessage({ type: endpoint, data: message });
    }
  }

  public stateUpdate(state: WebviewState) {
    this.postMessage("stateUpdate", state)
  }

  public resolveWebviewView(
    webviewView: vscode.WebviewView,
    context: vscode.WebviewViewResolveContext,
    _token: vscode.CancellationToken
  ) {
    let editor: vscode.TextEditor | undefined;
    this._view = webviewView;
    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [this._extensionUri],
    };
    webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);

    this.postMessage("stateUpdate", this.morph_language_client.getWebviewState())

    // Handles messages received from the webview
    webviewView.webview.onDidReceiveMessage(async (params: any) => {
      if (!this._view) throw new Error("no view");
      console.log("ChatProvider.ts received message: ", params);
      switch (params.type) {
        case "selectedAgentId":
          this.morph_language_client.sendSelectedAgentChange(params.selectedAgentId)
          break;
        case "copyText":
          console.log("recieved copy in webview");
          vscode.env.clipboard.writeText(params.content);
          vscode.window.showInformationMessage("Text copied to clipboard!");
          break;

        // Handle 'getAgents' message
        case "listAgents":
          this.morph_language_client.refreshWebviewAgents()
          break;
        // Handle 'runAgent' message
        case "runAgent":
          // console.log("Getting list of available agents")
          // let availableAgents: client.AgentRegistryItem[] = await this.morph_language_client.list_agents();
          console.log("runAgent ran");
          editor = vscode.window.activeTextEditor;
          if (!editor) {
            console.error("No active text editor found");
            return;
          }
          // get the uri and position of the current cursor
          let doc = editor.document;
          let textDocument = { uri: doc.uri.toString(), version: 0 };
          let position = editor.selection.active;

          const runAgentParams: RunAgentParams = {
            agent_type: params.params.agent_type,
            agent_params: { position, textDocument },
          };
          await this.morph_language_client.run(runAgentParams);
          break;

        case "chatMessage": {
          console.log("Sending publish message", `${params.agent_type}_${params.agent_id}_chat_request`);
          
          this.morph_language_client.sendChatHistoryChange(params.agent_id, params.messages)
          PubSub.pub(
            `${params.agent_type}_${params.agent_id}_chat_request`,
            params
          );

          break;
        }

        case "inputRequest": {
          console.log("Sending publish message", `${params.agent_type}_${params.agent_id}_input_request`);
          PubSub.pub(
            `${params.agent_type}_${params.agent_id}_input_request`,
            params
          );
          break;
        }
        case "restartAgent": {
          this.morph_language_client.restart_agent(params.agentId)
          break;
        }

        default:
          console.log("no case match for ", params.type, " in ChatProvider.ts");
      }
    });
  }

  public revive(panel: vscode.WebviewView) {
    this._view = panel;
  }

  private _getHtmlForWebview(webview: vscode.Webview) {
    const scriptUri = webview.asWebviewUri(
      vscode.Uri.joinPath(this._extensionUri, "out", `compiled/${this.name}.js`)
    );

    const cssUri = webview.asWebviewUri(
      vscode.Uri.joinPath(this._extensionUri, "out", `compiled/${this.name}.css`)
    );

    const stylesResetUri = webview.asWebviewUri(
      vscode.Uri.joinPath(this._extensionUri, "media", "reset.css")
    );

    const tailwindUri = webview.asWebviewUri(
      vscode.Uri.joinPath(
        this._extensionUri,
        "media",
        "scripts",
        "tailwind.min.js"
      )
    );

    const showdownUri = webview.asWebviewUri(
      vscode.Uri.joinPath(
        this._extensionUri,
        "media",
        "scripts",
        "showdown.min.js"
      )
    );

    const microlightUri = webview.asWebviewUri(
      vscode.Uri.joinPath(
        this._extensionUri,
        "media",
        "scripts",
        "microlight.min.js"
      )
    );

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
                    <script src="${microlightUri}" nonce="${nonce}"></script>
                    <link href="${cssUri}" rel="stylesheet">
                    <script nonce="${nonce}">
                        console.log("TESDKDFSJHALDFKDHSFLKJAHSFKJHSDAFL");
                        const vscode = acquireVsCodeApi();
                    </script>
                </head>
                <body class="p-0">
                </body>
                <script nonce="${nonce}" src="${scriptUri}"></script>
            </html>`;
  }
}
