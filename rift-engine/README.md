# ️🤖⚙️ Rift Code Engine

Rift Code Engine is an AI-first language server designed to power your personal, on-device AI software engineer. It is built and maintained by [Morph](https://morph.so).

## Installation

To install for development, run the following command from this directory:

```bash
pip install -e .
```

To install from PyPI, use:

```bash
pip install pyrift
```

After installation, add your OpenAI key by copying the example environment file:

```bash
cp .env_example .env
```

## Development

Use `conda` or `venv` to create and activate a Python virtual environment. Here are the detailed steps:

If you're using `pip install -e .conda`:
```bash
# Create a new conda environment
conda create --name myenv

# Activate the environment
conda activate myenv
```

If you're using `venv`:
```bash
# Create a new venv environment
python3 -m venv myenv

# Activate the environment
# On Windows, use:
myenv\Scripts\activate

# On Unix or MacOS, use:
source myenv/bin/activate
```

After activating the environment, install the package in editable mode:
```bash
pip install -e .
```

## Running

Run the server with `python -m rift.server.core --port 7797`. This will listen for LSP connections on port 7797.

Hot reloading + debug logging setup:

```bash
# pip install watchdog if not already installed
watchmedo shell-command \
    --patterns="*.py;*.txt" \
    --recursive \
    --command='python -m rift.server.core --port 7797 --debug True'  
```

Then run `python /rift-engine/rift/llm/test.py` in separate terminal.

## Contributing
[Fork](https://docs.github.com/en/get-started/quickstart/contributing-to-projects) this repository and make a pull request.

