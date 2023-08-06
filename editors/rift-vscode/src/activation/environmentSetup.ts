import * as path from "path";
import * as fs from "fs";
// import {getRiftServerUrl} from "../bridge";
import fetch from "node-fetch";
import * as vscode from "vscode";
import * as os from "os";
import fkill from "fkill";

import * as util from "util";
const exec = util.promisify(require("child_process").exec);
import { spawn } from "child_process";

const WINDOWS_REMOTE_SIGNED_SCRIPTS_ERROR =
    "A Python virtual enviroment cannot be activated because running scripts is disabled for this user. In order to use Rift, please enable signed scripts to run with this command in PowerShell: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`, reload VS Code, and then try again.";

const MAX_RETRIES = 3;

const RIFT_COMMIT = "ea0ee39bd86c331616bdaf3e8c02ed7c913b0933"
const PIP_INSTALL_COMMAND = `pip install "git+https://github.com/morph-labs/rift.git@${RIFT_COMMIT}#subdirectory=rift-engine&egg=pyrift"`
const PIP_INSTALL_ARGS = `install "git+https://github.com/morph-labs/rift.git@${RIFT_COMMIT}#subdirectory=rift-engine&egg=pyrift"`

const morphDir = path.join(os.homedir(), '.morph');

export function getExtensionUri(): vscode.Uri {
    return vscode.extensions.getExtension("morph.rift")!.extensionUri;
}

export async function ensureRift(): Promise<void> {
    console.log("Start - Checking if `rift` is in PATH.");

    let riftIsInPath = true;
    const command = process.platform === "win32" ? 'where' : 'which';

    console.log("Command set for 'which'/'where' based on platform.");

    console.log("Initiating 'exec' command to check for 'rift'.");
    try {
        const { stdout } = await exec(`${command} rift`);
        console.log("`exec` command executed successfully.");
        riftIsInPath = Boolean(stdout);
        console.log("Set 'riftIsInPath' based on command output.");
    } catch (error: any) {
        console.log("Exception caught while executing 'exec' command.", error);
        riftIsInPath = false;
        console.log("Set 'riftIsInPath' to false due to exception.");
    }
    const riftInMorphDir = fs.existsSync(path.join(morphDir, 'env', 'bin', 'rift'));

    if (!riftIsInPath && !riftInMorphDir) {
        console.error("`rift` executable not found in PATH or .morph/env/bin directory.");
        throw new Error("`rift` executable is not found in your PATH or .morph/env/bin. Please make sure it is correctly installed and try again.");
    }
    console.log("End - `rift` found in PATH or .morph/env/bin directory.");

}

// invoke this optionally via popup in case `ensureRift` fails
async function autoInstall() {
    console.log('Executing: const morphDir = path.join(os.homedir(), \'.morph\');');
    const morphDir = path.join(os.homedir(), '.morph');
    console.log('Executing: if (!fs.existsSync(morphDir))...');
    if (!fs.existsSync(morphDir)) {
        console.log('Executing: fs.mkdirSync(morphDir);');
        fs.mkdirSync(morphDir);
    }
    console.log('Executing: const pythonCommands = process.platform === "win32" ?...');
    const pythonCommands = process.platform === "win32" ? ['py -3.10', 'py -3', 'py'] : ['python3.10', 'python3', 'python'];
    console.log('Executing: let pythonCommand: string | null = null;');
    let pythonCommand: string | null = null;
    console.log('Executing: for... loop over pythonCommands');
    for (const command of pythonCommands) {
        console.log('Executing: const { stdout } = await exec(`${command} --version`);');
        const { stdout } = await exec(`${command} --version`);
        console.log('Executing: const versionMatch = stdout.match(/Python (\\d+\\.\\d+)/);');
        const versionMatch = stdout.match(/Python (\d+\.\d+)/);
        console.log('Executing: if (versionMatch)...');
        if (versionMatch) {
            console.log('Executing: const version = parseFloat(versionMatch[1]);');
            const version = parseFloat(versionMatch[1]);
            console.log('Executing: if (version >= 3.10)...');
            if (version >= 3.10) {
                console.log('Executing: pythonCommand = command;');
                pythonCommand = command;
                break;
            }
        }
    }
    console.log('Executing: if (pythonCommand === null)...');
    if (pythonCommand === null) {
        console.log('Throwing new Error(\'Python 3.10 or above is not found...\');');
        throw new Error('Python 3.10 or above is not found on your system. Please install it and try again.');
    }
    console.log('Executing: const createVenvCommand = `${pythonCommand}...`');
    const createVenvCommand = `${pythonCommand} -m venv ${morphDir}/env`;
    console.log('Executing: await exec(createVenvCommand);');
    await exec(createVenvCommand);

    console.log('Executing: const activateVenvAndInstallRiftCommand = `source...`');
    const activateVenvAndInstallRiftCommand = process.platform === "win32" ? `${morphDir}\\env\\Scripts\\pip ${PIP_INSTALL_ARGS}` :
        `${morphDir}/env/bin/pip ${PIP_INSTALL_ARGS}`;

    console.log('Executing: await exec(activateVenvAndInstallRiftCommand);');
    await exec(activateVenvAndInstallRiftCommand);
    console.log('autoInstall finished');
}

async function autoInstallHook() { await autoInstall().catch((error: any) => { vscode.window.showErrorMessage(`${error.message}\nTry installing Rift manually: https://www.github.com/morph-labs/rift`, "Close") }) }

export function ensureRiftHook() {
    // First, try to run ensureRift. upon catching an error, display a `vscode.window.showErrorMessage` with the caught error with a single selection choice called "Try auto install", then `.then` the promise, ensuring that the `selection` is equal to `Try auto install` and then rnning `autoInstall`.
    ensureRift().catch(e => {
        vscode.window
            .showErrorMessage(e.message, 'Try auto install')
            .then((selection) => {
                if (selection === 'Try auto install') {
                    autoInstallHook().then(
                        (_) => {
                            vscode.window.showInformationMessage("Rift installation successful.");
                            ensureRift().catch(
                                (e => { vscode.window.showErrorMessage(`unexpected error: ` + e.message + `\n Try installing Rift manually: https://www.github.com/morph-labs/rift`) })
                            )
                        }
                    ).catch((e) => vscode.window.showErrorMessage(`unexpected error: ` + e.message + `\n Try installing Rift manually: https://www.github.com/morph-labs/rift`))
                }
            });
    });
    vscode.commands.executeCommand('rift.start_server');
}

async function runRiftCodeEngine() {
    // try to execute rift command
    exec("rift").then(_ => { vscode.window.showInformationMessage("Rift Code Engine started successfully.") }).catch((_) => {
        console.log('Executing: Using Rift at custom path');
        // attempt to execute rift at custom path
        exec(`${morphDir}/env/bin/rift`).then(_ => { vscode.window.showInformationMessage("Rift Code Engine started successfully.") }).catch((e) => {
            // display error message 
            vscode.window.showErrorMessage("unexpected error: " + e.message + "\nTry installing Rift manually: https://www.github.com/morph-labs/rift");
        });
    });
}

vscode.commands.registerCommand('rift.start_server', runRiftCodeEngine);