import * as vscode from "vscode";
// import { MorphLanguageClient, RunChatParams } from "../client";
// import * as client from '../client'
import { getNonce } from "../getNonce";
import PubSub from "../lib/PubSub";
import type { MorphLanguageClient } from "../client";
import { ChatMessage, WebviewState } from "../types";

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
    public morph_language_client: MorphLanguageClient,
  ) { }

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
    this.postMessage("stateUpdate", state);
  }

  public resolveWebviewView(
    webviewView: vscode.WebviewView,
    context: vscode.WebviewViewResolveContext,
    _token: vscode.CancellationToken,
  ) {
    let editor: vscode.TextEditor | undefined;
    this._view = webviewView;
    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [this._extensionUri],
    };
    webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);

    this.postMessage(
      "stateUpdate",
      this.morph_language_client.getWebviewState(),
    );



    interface SelectedAgentIdMessage {
      readonly type: "selectedAgentId",
      readonly agentId: string
    }


    interface CopyTextMessage {
      type: "copyText",
      content: string
    }

    interface RunAgentParams {
      type: "runAgent"
      agent_type: string
    }

    interface ChatMessageParams {
      type: "chatMessage"
      agent_type: string,
      agent_id: string,
      messages: ChatMessage[]
    }
    interface InputRequestParams {
      type: "inputRequest"
      agent_type: string,
      agent_id: string,
    }

    interface ListAgentsParams {
      type: "listAgents"
    }
    interface RefreshStateParams {
      type: "refreshState"
    }
    interface FocusOmnibarParams {
      type: "focusOmnibar"
    }
    interface BlurOmnibarParams {
      type: "blurOmnibar"
    }

    interface RestartAgentParams {
      type: "restartAgent",
      agentId: string
    }
    interface SendHasNotificationChangeParams {
      type: "sendHasNotificationChange",
      agentId: string
      hasNotification: boolean
    }
    
    interface CancelAgentParams {
      type: 'cancelAgent'
      agentId: string
    }
    interface DeleteAgentParams {
      type: 'deleteAgent'
      agentId: string
    }



    type RegisteredMessageTypes = SelectedAgentIdMessage | CopyTextMessage | RunAgentParams | ChatMessageParams | ListAgentsParams | InputRequestParams | RestartAgentParams | RefreshStateParams | SendHasNotificationChangeParams | BlurOmnibarParams | FocusOmnibarParams | CancelAgentParams | DeleteAgentParams


    type MessageType = RegisteredMessageTypes 
    // Handles messages received from the webview
    webviewView.webview.onDidReceiveMessage(async (message: MessageType) => {
      if (!this._view) throw new Error("no view");
      console.log("WebviewProvider.ts received message: ", message);
      switch (message.type) {
        case "selectedAgentId":
          console.log(message.type)
          this.morph_language_client.sendSelectedAgentChange(message.agentId);
          break;
        case "copyText":
          // let msg = message as CopyTextMessage
          console.log("recieved copy in webview");
          vscode.env.clipboard.writeText(message.content);
          vscode.window.showInformationMessage("Text copied to clipboard!");
          break;

        // Handle 'getAgents' message
        case "listAgents":
          this.morph_language_client.refreshWebviewAgents();
          break;
        // Handle 'runAgent' message
        case "runAgent":
          // console.log("Getting list of available agents")
          // let availableAgents: client.AgentRegistryItem[] = await this.morph_language_client.list_agents();
          console.log("runAgent ran");

          const runAgentParams = {
            agent_type: message.agent_type,
          };
          await this.morph_language_client.run(runAgentParams);
          break;

        case "chatMessage": {
          console.log(
            "Sending publish message",
            `${message.agent_type}_${message.agent_id}_chat_request`,
          );

          this.morph_language_client.sendChatHistoryChange(
            message.agent_id,
            message.messages,
          );
          PubSub.pub(
            `${message.agent_type}_${message.agent_id}_chat_request`,
            message,
          );

          break;
        }

        case "inputRequest": {
          console.log(
            "Sending publish message",
            `${message.agent_type}_${message.agent_id}_input_request`,
          );
          PubSub.pub(
            `${message.agent_type}_${message.agent_id}_input_request`,
            message,
          );
          break;
        }
        case "restartAgent": {
          this.morph_language_client.restart_agent(message.agentId);
          break;
        }
        case "refreshState": {
          this.morph_language_client.refreshWebviewState();
          break;
        }
        case "sendHasNotificationChange": {
          this.morph_language_client.sendHasNotificationChange(
            message.agentId,
            message.hasNotification,
          );
          break;
        }

        case "focusOmnibar": {
          this.morph_language_client.focusOmnibar();
          break;
        }
        case "blurOmnibar": {
          this.morph_language_client.blurOmnibar();
          break;
        }
        case "cancelAgent":
          console.log('cancelAgent', message.agentId)
          this.morph_language_client.cancel({id: message.agentId});
          break;

        case "deleteAgent":
          console.log('delete agent', message.agentId)
          this.morph_language_client.delete({id: message.agentId});
          break;

        default:
          console.log(
            "no case match for ",
            message,
            " in WebviewProvider.ts",
          );
      }
    });
  }

  public revive(panel: vscode.WebviewView) {
    this._view = panel;
  }

  private _getHtmlForWebview(webview: vscode.Webview) {
    const scriptUri = webview.asWebviewUri(
      vscode.Uri.joinPath(
        this._extensionUri,
        "out",
        `compiled/${this.name}.js`,
      ),
    );

    const cssUri = webview.asWebviewUri(
      vscode.Uri.joinPath(
        this._extensionUri,
        "out",
        `compiled/${this.name}.css`,
      ),
    );

    const stylesResetUri = webview.asWebviewUri(
      vscode.Uri.joinPath(this._extensionUri, "media", "reset.css"),
    );

    const tailwindUri = webview.asWebviewUri(
      vscode.Uri.joinPath(
        this._extensionUri,
        "media",
        "scripts",
        "tailwind.min.js",
      ),
    );

    const showdownUri = webview.asWebviewUri(
      vscode.Uri.joinPath(
        this._extensionUri,
        "media",
        "scripts",
        "showdown.min.js",
      ),
    );

    const microlightUri = webview.asWebviewUri(
      vscode.Uri.joinPath(
        this._extensionUri,
        "media",
        "scripts",
        "microlight.min.js",
      ),
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
                        const vscode = acquireVsCodeApi();
                    </script>
                </head>
                <body class="p-0">
                </body>
                <script nonce="${nonce}" src="${scriptUri}"></script>
            </html>`;
  }
}
