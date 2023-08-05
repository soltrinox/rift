// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from "vscode";
import { MorphLanguageClient } from "./client";
// import { join } from 'path';

import { WebviewProvider } from "./elements/WebviewProvider";
export let chatProvider: WebviewProvider;
export let logProvider: WebviewProvider;
import { exec } from 'child_process';

export function dynamicImportAndActivate(context: vscode.ExtensionContext) {

    console.log('Extension "rift" is now active!');

    // Command to install pyrift
    exec('pip3 install pyrift', (error, stdout, stderr) => {
        if (error) {
            vscode.window.showErrorMessage(`Error installing pyrift: ${error.message}`);
            return;
        }
        console.log('rift installed!');

       
        exec('rift --version', (versionError, versionStdout, versionStderr) => {
            //if (versionError) {
            //    vscode.window.showErrorMessage(`Error getting pyrift version: ${versionError.message}`);
            //    return;
            //}
            const installedVersion = versionStdout.trim();
            const expectedVersion = 'X.X.X';  // TODO: JESSE

            //if (installedVersion !== expectedVersion) {
            //    vscode.window.showErrorMessage(`Version mismatch: Expected ${expectedVersion} but got ${installedVersion}`);
            //    return;
            //}

            console.log('Version check passed!');

            exec('rift', (pyriftError, pyriftStdout, pyriftStderr) => {
                if (pyriftError) {
                    vscode.window.showErrorMessage(`Error running rift: ${pyriftError.message}`);
                    return;
                }
                console.log('rift started!');
            });
        });
    });

}

// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {
  //dynamicImportAndActivate(context);
  let morph_language_client = new MorphLanguageClient(context);

  context.subscriptions.push(
    vscode.languages.registerCodeLensProvider("*", morph_language_client),
  );

  chatProvider = new WebviewProvider(
    "Chat",
    context.extensionUri,
    morph_language_client,
  );
  logProvider = new WebviewProvider(
    "Logs",
    context.extensionUri,
    morph_language_client,
  );

  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider("RiftChat", chatProvider, {
      webviewOptions: { retainContextWhenHidden: true },
    }),
  );
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider("RiftLogs", logProvider, {
      webviewOptions: { retainContextWhenHidden: true },
    }),
  );

  let recentlyOpenedFiles: string[] = [];
  vscode.workspace.onDidOpenTextDocument((document) => {
    const filePath = document.uri.fsPath;
    if (filePath.endsWith(".git")) return; // weirdly getting both file.txt and file.txt.git on every file change

    // Check if file path already exists in the recent files list
    const existingIndex = recentlyOpenedFiles.indexOf(filePath);

    // If the file is found, remove it from the current location
    if (existingIndex > -1) {
      recentlyOpenedFiles.splice(existingIndex, 1);
    }

    // Add the file to the end of the list (top of the stack)
    recentlyOpenedFiles.push(filePath);

    // Limit the history to the last 10 files
    if (recentlyOpenedFiles.length > 10) {
      recentlyOpenedFiles.shift();
    }

    morph_language_client.sendRecentlyOpenedFilesChange(recentlyOpenedFiles);
  });

  // const infoview = new Infoview(context)
  // context.subscriptions.push(infoview)

  // Use the console to output diagnostic information (console.log) and errors (console.error)
  // This line of code will only be executed once when your extension is activated
  console.log('Congratulations, your extension "rift" is now active!');

  // The command has been defined in the package.json file
  // Now provide the implementation of the command with registerCommand
  // The commandId parameter must match the command field in package.json

  let disposablefocusOmnibar = vscode.commands.registerCommand(
    "rift.focus_omnibar",
    async () => {
      // vscode.window.createTreeView("RiftChat", chatProvider)
      vscode.commands.executeCommand("RiftChat.focus");

      morph_language_client.focusOmnibar();
    },
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("rift.reset_chat", () => {
      morph_language_client.restartActiveAgent();
    }),
  );

  context.subscriptions.push(disposablefocusOmnibar);
  context.subscriptions.push(morph_language_client);
}

// This method is called when your extension is deactivated
export function deactivate() {}
