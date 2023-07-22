// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from "vscode";
import { MorphLanguageClient, AgentProgress } from "./client";
// import { join } from 'path';
// import { TextDocumentIdentifier } from 'vscode-languageclient';
import { WebviewProvider } from "./elements/WebviewProvider";


export let chatProvider: WebviewProvider;
export let logProvider: WebviewProvider;
// export let morph_language_client: MorphLanguageClient;

// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {
  let morph_language_client = new MorphLanguageClient(context);

  context.subscriptions.push(
    vscode.languages.registerCodeLensProvider("*", morph_language_client)
  );

  chatProvider = new WebviewProvider("Chat", context.extensionUri, morph_language_client);
  logProvider = new WebviewProvider("Logs", context.extensionUri, morph_language_client);

  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider("RiftChat", chatProvider, {webviewOptions: {retainContextWhenHidden: true}})
  );
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider("RiftLogs", logProvider, {webviewOptions: {retainContextWhenHidden: true}})
  );
  // const infoview = new Infoview(context)
  // context.subscriptions.push(infoview)

  // Use the console to output diagnostic information (console.log) and errors (console.error)
  // This line of code will only be executed once when your extension is activated
  console.log('Congratulations, your extension "rift" is now active!');

  // The command has been defined in the package.json file
  // Now provide the implementation of the command with registerCommand
  // The commandId parameter must match the command field in package.json
  let disposable = vscode.commands.registerCommand(
    "rift.run_agent",
    async () => {
      // get the current active cursor position
      const editor = vscode.window.activeTextEditor;
      if (!editor) {
        console.error("No active text editor found");
        return;
      }
      // get the uri and position of the current cursor
      const doc = editor.document;
      const textDocument = { uri: doc.uri.toString(), version: 0 };
      const position = editor.selection.active;
      // let instructionPrompt = await vscode.window.showInputBox({
      //     ignoreFocusOut: true,
      //     placeHolder: 'Write the function body',
      //     prompt: 'Enter a description of what you want the agent to do...',
      // });
      // if (instructionPrompt === undefined) {
      //     console.log('run_agent task was cancelled')
      //     return
      // }

      const default_request_input_callback = async (params: any) => {
        let response = await vscode.window.showInputBox({
          ignoreFocusOut: true,
          placeHolder: params.place_holder,
          prompt: params.msg,
        });
        return { response: response };
      };

      const default_send_update_callback = async (params: any) => {
        vscode.window.showInformationMessage(params.msg);
      };

      // const code_completion_send_progress_callback = async (params: any) => {
      //     const green = vscode.window.createTextEditorDecorationType({ backgroundColor: 'rgba(0,255,0,0.1)' })
      //     const key: string = `code_completion_${params.agent_id}`
      //     if (params.tasks) {
      //         logProvider.postMessage("tasks", { agent_id: params.agent_id, ...params.tasks })
      //         if (params.tasks.task.status) {
      //             if (morph_language_client.agentStates.get(key).status !== params.tasks.task.status) {
      //                 morph_language_client.agentStates.get(key).status = params.tasks.task.status
      //                 morph_language_client.agentStates.get(key).emitter.fire(params.tasks.task.status)
      //             }
      //         }
      //     }
      //     if (params.payload) {
      //         if (params.payload.ranges) {
      //             morph_language_client.agentStates.get(key).ranges = params.payload.ranges
      //         }
      //     }
      //     const editors = vscode.window.visibleTextEditors.filter(e => e.document.uri.toString() == morph_language_client.agentStates.get(key).params.textDocument.uri.toString())
      //     for (const editor of editors) {
      //         // [todo] check editor is visible
      //         const version = editor.document.version
      //         if (params.tasks) {
      //             if (params.tasks.task.status == 'accepted' || params.tasks.task.status == 'rejected') {
      //                 editor.setDecorations(green, [])
      //                 continue
      //             }
      //         }
      //         if (params.payload) {
      //             if (params.payload.ranges) {
      //                 editor.setDecorations(green, params.payload.ranges.map(r => new vscode.Range(r.start.line, r.start.character, r.end.line, r.end.character)))
      //             }
      //         }
      //     }
      // }

      const r = await morph_language_client.run(
        {
          agent_type: "code_completion",
          agent_params: { position, textDocument },
        }
        // default_request_input_callback, // handle incoming requests
        // async () => { }, // code_completion agents don't request chat
        // default_send_update_callback, // handle incoming text notifications
        // code_completion_send_progress_callback, // handle task progress updates / streaming results
        // async () => { } // code_completion agents use custom logic for accept/reject of final diffs
      );
    }
  );

  // context.subscriptions.push(
  //     vscode.languages.registerCodeLensProvider('*', morph_language_client)
  // )
  context.subscriptions.push(disposable);
  context.subscriptions.push(morph_language_client);

  // const provider = async (document, position, context, token) => {
  //     return [
  //         { insertText: await mlc.provideInlineCompletionItems(document, position, context, token) }
  //     ]
  // };
}

// This method is called when your extension is deactivated
export function deactivate() {}
