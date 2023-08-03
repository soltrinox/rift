import * as vscode from "vscode";
import {getExtensionVersion, startRiftPythonServer,} from "./environmentSetup";

const PACKAGE_JSON_RAW_GITHUB_URL =
    "https://raw.githubusercontent.com/riftdev/rift/HEAD/extension/package.json";

export let extensionContext: vscode.ExtensionContext | undefined = undefined;
import fetch from 'node-fetch';

function getExtensionVersionInt(versionString: string): number {
    return parseInt(versionString.replace(/\./g, ""));
}

export async function activateExtension(context: vscode.ExtensionContext) {
    extensionContext = context;
    console.log("Using Rift version: ", getExtensionVersion());
    try {
        console.log(
            "In workspace: ",
            vscode.workspace.workspaceFolders?.[0].uri.fsPath
        );
    } catch (e) {
        console.log("Error getting workspace folder: ", e);
    }
    // Before anything else, check whether this is an out-of-date version of the extension
    // Do so by grabbing the package.json off of the GitHub respository for now.
    /** 
    await fetch(PACKAGE_JSON_RAW_GITHUB_URL)
         .then(async (res) => res.json())
         .then((packageJson) => {
             const n1 = getExtensionVersionInt(packageJson.version);
             const n2 = getExtensionVersionInt(getExtensionVersion());
             if (Math.abs(n1 - n2) > 1) {
                 // Accept up to 1 version difference
                 vscode.window.showInformationMessage(
                     `You are using an out-of-date version of the Rift extension. Please update to the latest version.`
                 );
             }
         })
         .catch((e) => console.log("Error checking for extension updates: ", e));
    **/
     // Register commands and providers
    // registerAllCodeLensProviders(context);
    // registerAllCommands(context);
    // registerQuickFixProvider();

    // Start the server and display loader if taking > 2 seconds
    const sessionIdPromise = (async () => {
        await new Promise((resolve) => {
            let serverStarted = false;

            // Start the server and set serverStarted to true when done
            startRiftPythonServer().then(() => {
                serverStarted = true;
                resolve(null);
            });

            // Wait for 2 seconds
            setTimeout(() => {
                // If the server hasn't started after 2 seconds, show the notification
                if (!serverStarted) {
                    vscode.window.withProgress(
                        {
                            location: vscode.ProgressLocation.Notification,
                            title:
                                "Starting Rift Server... (it may take a minute to download Python packages)",
                            cancellable: false,
                        },
                        async (progress, token) => {
                            // Wait for the server to start
                            while (!serverStarted) {
                                await new Promise((innerResolve) =>
                                    setTimeout(innerResolve, 1000)
                                );
                            }
                            return Promise.resolve();
                        }
                    );
                }
            }, 2000);
        });

        console.log("Rift server started");
    })();
}