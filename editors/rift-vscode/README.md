# Rift VSCode Extension

Rift is an AI-native language server and extension that lets you deploy a personal AI software engineer — locally hosted, private, secure, and free.

Rift and this extension are fully [open-source](https://github.com/morph-labs/rift/tree/main/editors/rift-vscode).

## About

The future of AI code assistants is open-source, private, secure, and on-device. Rift understands, explains, and writes code with language models that run entirely on your device using the open source [Rift Code Engine](https://github.com/morph-labs/rift/tree/main/rift-engine).

## Installation

From the VSCode Marketplace:

- Click on the extension icon in the sidebar
- Search for "Rift"
- Click the install button.

For development / testing:

```bash
bash reinstall.sh
```

## Usage

1. Ensure the [Rift Code Engine](https://github.com/morph-labs/rift/tree/main/rift-engine) is installed and running on port 7797:

```bash
git clone https://www.github.com/morph-labs/rift
cd rift

# set up a virtual environment with Python (>=3.9), then install the `rift` Python package
pip install -e ./rift-engine

# launch the language server
python -m rift.server.core --host 127.0.0.1 --port 7797
```

This requires a working Python (>=3.9) installation. 2. Access the chat interface by clicking on the sidebar icon. 3. Trigger code completions in the editor window using the keyboard shortcut (`Ctrl + M`) or by running the `Rift: Code Completion` command (`Ctrl + Shift + P` + type "Rift"). If the extension is unable to connect to the server, try running the command `Developer: Reload Window`

## Development

See [here](https://github.com/morph-labs/rift/blob/main/editors/rift-vscode/CONTRIBUTING.md) for instructions on how to develop this extension.

## Project Structure

The `rift-vscode` project is structured as follows:

- `src/`: This directory contains the TypeScript source code for the extension.
  - `client.ts`: This is the main entry point for the extension. It sets up the connection to the Rift language server and handles communication between VSCode and the server.
  - `elements/`: This directory contains custom web components used in the extension's UI.
    - `WebviewProvider.svelte`: This Svelte component is responsible for rendering the webview UI for the extension. It communicates with the VSCode API to send and receive messages from the extension.
    - `Chat.svelte`: This Svelte component renders the chat interface for interacting with the Rift language server.
    - `CodeEditor.svelte`: This Svelte component renders a code editor within the webview. It uses the Monaco Editor library to provide a rich code editing experience.
- `media/`: This directory contains static assets such as images and stylesheets.
- `test/`: This directory contains tests for the extension.
- `package.json`: This file defines the extension's dependencies and scripts.
- `tsconfig.json`: This file configures the TypeScript compiler for the project.
