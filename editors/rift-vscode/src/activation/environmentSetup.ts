import * as path from "path";
import * as fs from "fs";
// import {getRiftServerUrl} from "../bridge";
import fetch from "node-fetch";
import * as vscode from "vscode";
import * as os from "os";
import fkill from "fkill";

const util = require("util");
const exec = util.promisify(require("child_process").exec);
const {spawn} = require("child_process");

const WINDOWS_REMOTE_SIGNED_SCRIPTS_ERROR =
    "A Python virtual enviroment cannot be activated because running scripts is disabled for this user. In order to use Rift, please enable signed scripts to run with this command in PowerShell: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`, reload VS Code, and then try again.";

const MAX_RETRIES = 3;


export function getExtensionUri(): vscode.Uri {
    return vscode.extensions.getExtension("morph.rift")!.extensionUri;
}

async function retryThenFail(
    fn: () => Promise<any>,
    retries: number = MAX_RETRIES
): Promise<any> {
    try {
        if (retries < MAX_RETRIES && process.platform === "win32") {
            let [stdout, stderr] = await runCommand("Get-ExecutionPolicy");
            if (!stdout.includes("RemoteSigned")) {
                [stdout, stderr] = await runCommand(
                    "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser"
                );
                console.log("Execution policy stdout: ", stdout);
                console.log("Execution policy stderr: ", stderr);
            }
        }

        return await fn();
    } catch (e: any) {
        if (retries > 0) {
            return await retryThenFail(fn, retries - 1);
        }

        // Show corresponding error message depending on the platform
        let msg =
            "Failed to set up Rift extension. Please email hi@rift.dev and we'll get this fixed ASAP!";
        try {
            switch (process.platform) {
                case "win32":
                    msg = WINDOWS_REMOTE_SIGNED_SCRIPTS_ERROR;
                    break;
                case "darwin":
                    break;
                case "linux":
                    const [pythonCmd] = await getPythonPipCommands();
                    msg = await getLinuxAptInstallError(pythonCmd);
                    break;
            }
        } finally {
            console.log("After retries, failed to set up Rift extension", msg);
            vscode.window
                .showErrorMessage(msg, "View Logs", "Retry")
                .then((selection) => {
                    if (selection === "View Logs") {
                        vscode.commands.executeCommand("rift.viewLogs");
                    } else if (selection === "Retry") {
                        // Reload VS Code window
                        vscode.commands.executeCommand("workbench.action.reloadWindow");
                    }
                });
        }

        throw e;
    }
}

async function runCommand(cmd: string): Promise<[string, string | undefined]> {
    console.log("Running command: ", cmd);
    var stdout: any = "";
    var stderr: any = "";
    try {
        var {stdout, stderr} = await exec(cmd, {
            shell: process.platform === "win32" ? "powershell.exe" : undefined,
        });
    } catch (e: any) {
        stderr = e.stderr;
        stdout = e.stdout;
    }
    if (stderr === "") {
        stderr = undefined;
    }
    if (typeof stdout === "undefined") {
        stdout = "";
    }

    return [stdout, stderr];
}

export async function getPythonPipCommands() {
    var [stdout, stderr] = await runCommand("python3 --version");
    let pythonCmd = "python3";
    if (stderr) {
        // If not, first see if python3 is aliased to python
        var [stdout, stderr] = await runCommand("python --version");
        if (
            (typeof stderr === "undefined" || stderr === "") &&
            stdout.split(" ")[1][0] === "3"
        ) {
            // Python3 is aliased to python
            pythonCmd = "python";
        } else {
            // Python doesn't exist at all
            vscode.window.showErrorMessage(
                "Rift requires Python3. Please install from https://www.python.org/downloads, reload VS Code, and try again."
            );
            throw new Error("Python 3 is not installed.");
        }
    }

    let pipCmd = pythonCmd.endsWith("3") ? "pip3" : "pip";

    const version = stdout.split(" ")[1];
    const [major, minor] = version.split(".");
    if (parseInt(major) !== 3 || parseInt(minor) < 8) {
        // Need to check specific versions
        const checkPython3VersionExists = async (minorVersion: number) => {
            const [stdout, stderr] = await runCommand(
                `python3.${minorVersion} --version`
            );
            return typeof stderr === "undefined" || stderr === "";
        };

        //TODO does rift actually work with python 3.9?
        const VALID_VERSIONS = [9, 10, 11, 12];
        let versionExists = false;

        for (const minorVersion of VALID_VERSIONS) {
            if (await checkPython3VersionExists(minorVersion)) {
                versionExists = true;
                pythonCmd = `python3.${minorVersion}`;
                pipCmd = `pip3.${minorVersion}`;
            }
        }

        if (!versionExists) {
            vscode.window.showErrorMessage(
                "Rift requires Python version 3.9 or greater. Please update your Python installation, reload VS Code, and try again."
            );
            throw new Error("Python3.9 or greater is not installed.");
        }
    }

    return [pythonCmd, pipCmd];
}

function getActivateUpgradeCommands(pythonCmd: string, pipCmd: string) {
    let pipUpgradeCmd = `${pipCmd} install --upgrade pip`;
    if (process.platform == "win32") {
        pipUpgradeCmd = `${pythonCmd} -m pip install --upgrade pip`;
    }
    return [pipUpgradeCmd];
}




async function getLinuxAptInstallError(pythonCmd: string) {
    // First, try to run the command to install python3-venv
    let [stdout, stderr] = await runCommand(`${pythonCmd} --version`);
    if (stderr) {
        await vscode.window.showErrorMessage(
            "Python3 is not installed. Please install from https://www.python.org/downloads, reload VS Code, and try again."
        );
        throw new Error(stderr);
    }
    const version = stdout.split(" ")[1].split(".")[1];
    const installVenvCommand = `apt-get install python3.${version}-venv`;
    await runCommand("apt-get update");
    return `[Important] Rift needs to create a Python virtual environment, but python3.${version}-venv is not installed. Please run this command in your terminal: \`${installVenvCommand}\`, reload VS Code, and then try again.`;
}

async function createPythonVenv(pythonCmd: string) {
     const createEnvCommand = [
            `${pythonCmd} -m venv env`,
        ].join(" ; ");

        const [stdout, stderr] = await runCommand(createEnvCommand);
        if (
            stderr &&
            stderr.includes("running scripts is disabled on this system")
        ) {
            console.log("Scripts disabled error when trying to create env");
            await vscode.window.showErrorMessage(WINDOWS_REMOTE_SIGNED_SCRIPTS_ERROR);
            throw new Error(stderr);
        } else if (
            stderr?.includes("On Debian/Ubuntu systems") ||
            stdout?.includes("On Debian/Ubuntu systems")
        ) {
            const msg = await getLinuxAptInstallError(pythonCmd);
            console.log(msg);
            await vscode.window.showErrorMessage(msg);
        } else if (
            stderr?.includes("Permission denied") &&
            stderr?.includes("python.exe")
        ) {
            // This might mean that another window is currently using the python.exe file to install requirements
            // So we want to wait and try again
            let i = 0;
            await new Promise((resolve, reject) =>
                setInterval(() => {
                    if (i > 5) {
                        reject("Timed out waiting for other window to create env...");
                    } else {
                        console.log("Waiting for other window to create env...");
                    }
                    i++;
                }, 5000)
            );
        } else {
            const msg = [
                "Python environment not successfully created. Trying again. Here was the stdout + stderr: ",
                `stdout: ${stdout}`,
                `stderr: ${stderr}`,
            ].join("\n\n");
            console.log(msg);
            throw new Error(msg);
        }
}

async function setupPythonEnv() {
    console.log("Setting up python env for Rift extension...");

    const [pythonCmd, pipCmd] = await getPythonPipCommands();
    const [, pipUpgradeCmd] = getActivateUpgradeCommands(
        pythonCmd,
        pipCmd
    );

    await retryThenFail(async () => {
        // First, create the virtual environment
        await createPythonVenv(pythonCmd);

        // Install the requirements
        const installRequirementsCommand = [
                pipUpgradeCmd,
                `${pipCmd} install git+https://github.com/morph-labs/rift.git#egg=version_subpkg&subdirectory=rift-engine`,
            ].join(" ; ");
            const [, stderr] = await runCommand(installRequirementsCommand);
            if (stderr) {
                throw new Error(stderr);
            }
            // Write the version number for which requirements were installed
            //fs.writeFileSync(requirementsVersionPath(), getExtensionVersion());
        
    });
}

function readEnvFile(path: string) {
    if (!fs.existsSync(path)) {
        return {};
    }
    let envFile = fs.readFileSync(path, "utf8");

    let env: { [key: string]: string } = {};
    envFile.split("\n").forEach((line) => {
        let [key, value] = line.split("=");
        if (typeof key === "undefined" || typeof value === "undefined") {
            return;
        }
        env[key] = value.replace(/"/g, "");
    });
    return env;
}

function writeEnvFile(path: string, key: string, value: string) {
    if (!fs.existsSync(path)) {
        fs.writeFileSync(path, `${key}="${value}"`);
        return;
    }

    let env = readEnvFile(path);
    env[key] = value;

    let newEnvFile = "";
    for (let key in env) {
        newEnvFile += `${key}="${env[key]}"\n`;
    }
    fs.writeFileSync(path, newEnvFile);
}

async function checkServerRunning(serverUrl: string): Promise<boolean> {
    // Check if already running by calling /health
    try {
        const response = await fetch(serverUrl + "/health");
        if (response.status === 200) {
            console.log("Rift python server already running");
            return true;
        } else {
            return false;
        }
    } catch (e) {
        return false;
    }
}


export function getExtensionVersion() {
    console.log(vscode.extensions);
    const extension = vscode.extensions.getExtension("morph.rift");
    return extension?.packageJSON.version || "";
}

export async function startRiftPythonServer() {
    // Check vscode settings
    const serverUrl = "http://localhost:7797"

    // setupServerPath();

    return await retryThenFail(async () => {
        console.log("Checking if server is old version");
        //TODO: Kill the server if it is running an old version
        /*if (!(await checkServerRunning(serverUrl))) {
            console.log("Killing old server...");
        try {
            await fkill(":7797");
        } catch (e: any) {
            if (!e.message.includes("Process doesn't exist")) {
                console.log("Failed to kill old server:", e);
            }
            */

        setupPythonEnv();
        // Spawn the server process on port 65432
        const [pythonCmd] = await getPythonPipCommands();

        const command = `pip install rift | rift`;

        return new Promise(async (resolve, reject) => {
            console.log("Starting Rift python server...   "+command);
            try {
                const child = spawn(command, {
                    shell: true,
                });
                child.stderr.on("data", (data: any) => {
                    if (
                        data.includes("rift")
                    ) {
                        console.log("MYDATA"+data)
                        console.log("Successfully started Rift python server");
                        resolve(null);
                    } else if (data.includes("ERROR") || data.includes("Traceback")) {
                        console.log("Error starting Rift python server: ", data);
                    } else {
                        console.log(`stdout: ${data}`);
                    }
                });
                child.on("error", (error: any) => {
                    console.log(`error: ${error.message}`);
                });

                child.on("close", (code: any) => {
                    console.log(`child process exited with code ${code}`);
                });

                child.stdout.on("data", (data: any) => {
                    console.log(`stdout: ${data}`);
                });

            } catch (e) {
                console.log("Failed to start Rift python server", e);
                // If failed, check if it's because the server is already running (might have happened just after we checked above)
                if (await checkServerRunning(serverUrl)) {
                    resolve(null);
                } else {
                    reject();
                }
            }
        });
    });
}

export async function downloadPython3() {
    // Download python3 and return the command to run it (python or python3)
    let os = process.platform;
    let command: string = "";
    let pythonCmd = "python3";
    if (os === "darwin") {
        throw new Error("python3 not found");
    } else if (os === "linux") {
        command =
            "sudo apt update ; upgrade ; sudo apt install python3 python3-pip";
    } else if (os === "win32") {
        command =
            "wget -O python_installer.exe https://www.python.org/ftp/python/3.11.3/python-3.11.3-amd64.exe ; python_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0";
        pythonCmd = "python";
    }

    var [stdout, stderr] = await runCommand(command);
    if (stderr) {
        throw new Error(stderr);
    }
    console.log("Successfully downloaded python3");

    return pythonCmd;
}
