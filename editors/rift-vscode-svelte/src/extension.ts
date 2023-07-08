// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';
import { MorphLanguageClient } from './client';
// import { join } from 'path';
// import { TextDocumentIdentifier } from 'vscode-languageclient';
import { ChatProvider } from './elements/ChatProvider';
// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {
    // const infoview = new Infoview(context)
    // context.subscriptions.push(infoview)

    // Use the console to output diagnostic information (console.log) and errors (console.error)
    // This line of code will only be executed once when your extension is activated
    console.log('Congratulations, your extension "rift" is now active!');

    // The command has been defined in the package.json file
    // Now provide the implementation of the command with registerCommand
    // The commandId parameter must match the command field in package.json
    let disposable = vscode.commands.registerCommand('rift.run_agent', async () => {
        // get the current active cursor position
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            console.error('No active text editor found');
            return
        }
        // get the uri and position of the current cursor
        const doc = editor.document;
        const textDocument = { uri: doc.uri.toString(), version: 0 }
        const position = editor.selection.active;
        let instructionPrompt = await vscode.window.showInputBox({
            ignoreFocusOut: true,
            placeHolder: 'Write the function body',
            prompt: 'Enter a description of what you want the agent to do...',
        });
        if (instructionPrompt === undefined) {
            console.log('run_agent task was cancelled')
            return
        }
        //
        // let CODE_COMPLETION_STATUS: string = "running";
        // let CODE_COMPLETION_RANGES: vscode.Range[] = [];
        // let STATUS_CHANGE_EMITTER = new vscode.EventEmitter<AgentStatus>;
        const code_completion_send_progress_callback = async (params: AgentProgress) => {
            console.log(`PROGRESS PARAMS: ${params}`)
            const green = vscode.window.createTextEditorDecorationType({ backgroundColor: 'rgba(0,255,0,0.1)' })
            const key: string = `code_completion_${params.agent_id}`
            if (params.tasks) {
                console.log("TASKS: ", params.tasks)
                if (params.tasks.task.status) {
                    if (hslc.agentStates.get(key).status !== params.tasks.task.status) {
                        hslc.agentStates.get(key).status = params.tasks.task.status
                        hslc.agentStates.get(key).emitter.fire(params.tasks.task.status)
                    }
                }
            }
            if (params.payload) {
                if (params.payload.ranges) {
                    hslc.agentStates.get(key).ranges = params.payload.ranges
                }
            }
            const editors = vscode.window.visibleTextEditors.filter(e => e.document.uri.toString() == hslc.agentStates.get(key).params.textDocument.uri.toString())
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

        const r = await hslc.run(
            {
                agent_type: "code_completion",
                agent_params: { position, textDocument, instructionPrompt }
            },
            async () => {},
            async () => {},
            code_completion_send_progress_callback,
            async () => {}
        )
    }
    );

    context.subscriptions.push(disposable);

    let hslc = new MorphLanguageClient(context)
    context.subscriptions.push(hslc)
    // const provider = async (document, position, context, token) => {
    //     return [
    //         { insertText: await hslc.provideInlineCompletionItems(document, position, context, token) }
    //     ]
    // };

    // context.subscriptions.push(
    //     vscode.languages.registerInlineCompletionItemProvider(
    //         { pattern: "*" },
    //         { provideInlineCompletionItems: provider }
    //     )
    // );

    context.subscriptions.push(
        vscode.languages.registerCodeLensProvider('*', hslc)
    )
    const chatProvider = new ChatProvider(context.extensionUri, hslc);

    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider("RiftChat", chatProvider)
    );
}


// This method is called when your extension is deactivated
export function deactivate() { }
