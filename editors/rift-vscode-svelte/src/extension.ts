// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';
import { MorphLanguageClient } from './client';
import { join } from 'path';
import { TextDocumentIdentifier } from 'vscode-languageclient';
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
        let task = await vscode.window.showInputBox({
            ignoreFocusOut: true,
            placeHolder: 'Write the function body',
            prompt: 'Enter a description of what you want the agent to do...',
        });
        if (task === undefined) {
            console.log('run_agent task was cancelled')
            return
        }
        const r = await hslc.run_agent({ position, textDocument, task })
    });

    context.subscriptions.push(disposable);

    let hslc = new MorphLanguageClient(context)
    context.subscriptions.push(hslc)
    const provider = async (document, position, context, token) => {
        return [
            { insertText: await hslc.provideInlineCompletionItems(document, position, context, token) }
        ]
    };

    context.subscriptions.push(
        vscode.languages.registerInlineCompletionItemProvider(
            { pattern: "*" },
            { provideInlineCompletionItems: provider }
        )
    );

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
