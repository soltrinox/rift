# Rift

Rift is an open-source AI-native [language server](https://microsoft.github.io/language-server-protocol/) for the development environments of the future. Software will soon be written mostly by AI software engineers that work alongside you. Rift makes your IDE *agentic*. The codebases of the future will be living, spatial artifacts that *anticipate*, *listen to*, *maintain context*, *react to*, and *execute* your every intent. Rift is the software infrastructure for that future.

The [Rift Code Engine](./rift-engine/) implements an AI-native extension of the language server protocol. The [Rift VSCode extension](./editors/rift-vscode) implements a client and end-user application

<!-- TODO: color on the value prop of using Rift and what Rift unlocks -- find a way to introduce the concept of an agentic IDE -->

We provide a reference implementation of the Rift protocol with the [Rift VSCode extension](./editors/rift-vscode).

![rift screencast](assets/rift-screencast.gif)

- [Discord](https://discord.gg/wa5sgWMfqv)
/- [Getting started](#getting-started)
- [Features](#features)
- [Usage](#usage)
- [Tips](#tips)
- [Installation](#installation)
- [FAQ](#faq)


<!-- ## The road ahead -->
<!-- Existing code generation tooling is presently mostly code-agnostic, operating at the level of tokens in / tokens out of code LMs. The [language server protocol](https://microsoft.github.io/language-server-protocol/) (LSP) defines a standard for *language servers*, objects which index a codebase and provide structure- and runtime-aware interfaces to external development tools like IDEs. -->

<!-- The Rift Code Engine is an AI-native language server which will expose interfaces for code transformations and code understanding in a uniform, model- and language-agnostic way --- e.g. `rift.summarize_callsites` or `rift.launch_ai_swe_async` should work on a Python codebase with [StarCoder](https://huggingface.co/blog/starcoder) as well as it works on a Rust codebase using [CodeGen](https://github.com/salesforce/CodeGen). Within the language server, models will have full programatic access to language-specific tooling like compilers, unit and integration test frameworks, and static analyzers to produce correct code with minimal user intervention. We will develop UX idioms as needed to support this functionality in the Rift IDE extensions. -->

## Features
Rift makes your IDE *agentic*. With an AI-native language server, your 

## Getting started
Install the VSCode extension from the VSCode Marketplace. By default, the extension will attempt to automatically start the Rift Code Engine every time the extension is activated. During this process, if the `rift` executable is not found, the extension will ask you to attempt an automatic installation of a Python environment and the Rift Code Engine. To disable this behavior, such as for development, go to the VSCode settings, search for "rift", and set `rift.autostart` to `false`.

If the automatic installation of the Rift Code Engine fails, follow the below instructions for manual installation.

### Manual installation
**Rift Code Engine**:
- Set up a Python virtual environment for Python 3.10 or higher.
  - On Mac OSX:
    - Install [homebrew](https://brew.sh).
    - `brew install python@3.10`
    - `mkdir ~/.morph/ && cd ~/.morph/ && python3.10 -m venv env`
    - `source ./env/bin/activate/`
  - On Linux:
    - On Ubuntu:
      - `sudo apt install software-properties-common -y`
      - `sudo add-apt-repository ppa:deadsnakes/ppa`
      - `sudo apt install python3.10 && sudo apt install python3.10-venv`
      - `mkdir ~/.morph/ && cd ~/.morph/ && python3.10 -m venv env`
      - `source ./env/bin/activate/`
    - On Arch:
      - `yay -S python310`
      - `mkdir ~/.morph/ && cd ~/.morph/ && python3.10 -m venv env`
      - `source ./env/bin/activate/`
- Install Rift.
  - Make sure that `which pip` returns a path whose prefix matches the location of a virtual environment, such as the one installed above.
  - Using `pip` and PyPI:
    - `pip install --upgrade pyrift`
  - Using `pip` from GitHub:
    - `pip install "git+https://github.com/morph-labs/rift.git@ea0ee39bd86c331616bdaf3e8c02ed7c913b0933#egg=pyrift&subdirectory=rift-engine"`
  - From source:
    - `cd ~/.morph/ && git clone git@github.com:morph-labs/rift && cd ./rift/rift-engine/ && pip install -e .`
      
**Rift VSCode Extension** (via `code --install-extension`, change the executable as needed):
- `cd ./editors/rift-vscode && npm i && bash reinstall.sh`



## Contributing
We welcome contributions to Rift at all levels of the stack, for example:
- adding support for new open-source models in the Rift Code Engine
- implementing the Rift API for your favorite programming language
- UX polish in the VSCode extension
- adding support for your favorite editor.

See our [contribution guide](/CONTRIBUTORS.md) for details and guidelines.

Programming is evolving. Join the [community](https://discord.gg/wa5sgWMfqv), contribute to our roadmap, and help shape the future of software.

