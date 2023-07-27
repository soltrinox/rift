# Contributing to the Rift VSCode Extension

Love Rift and want to get involved? You're in the right place!

## Table of Contents

* [How to Contribute](#how-to-contribute)
  * [Report Bugs](#report-bugs)
  * [Suggest Features](#suggest-features)
  * [Update Docs](#update-docs)
  * [Write Code](#write-code)
* [VSCode Extension Setup](#vscode-extension-setup)
* [Architecture](#architecture)

## How to Contribute

### Report Bugs
[Create an issue](https://github.com/morph-labs/rift/issues) for any bugs you find. Be sure to be descriptive!

### Suggest Features
[Create an issue](https://github.com/morph-labs/rift/issues) for any features you'd like to see implemented.

### Update Docs
TODO

### Write Code
Feel free to [tackle an issue](https://github.com/morph-labs/rift/issues)

## VSCode Extension Setup
TODO

## Architecture

The following output is the directory structure and organization of rift-vscode:

```sh
tree -I 'node_modules|out|dist'
```

```sh
.
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── README.md
├── build
│   └── node-extension.webpack.config.cjs
├── media
│   ├── icon.svg
│   ├── icons
│   │   ├── resetDark.svg
│   │   └── resetLight.svg
│   ├── reset.css
│   ├── scripts
│   │   ├── microlight.min.js
│   │   ├── showdown.min.js
│   │   └── tailwind.min.js
│   └── vscode.css
├── package-lock.json
├── package.json
├── resources
│   ├── icon.png
│   ├── icon.svg
│   ├── iconold.png
│   └── vsce-icon.png
├── rollup.config.js
├── src
│   ├── client.ts
│   ├── elements
│   │   └── WebviewProvider.ts
│   ├── extension.ts
│   ├── getNonce.ts
│   ├── lib
│   │   ├── PubSub.ts
│   │   └── Store.ts
│   ├── test
│   │   ├── runTest.ts
│   │   └── suite
│   │       ├── extension.test.ts
│   │       └── index.ts
│   └── types.ts
├── tsconfig.json
├── vsc-extension-quickstart.md
├── webpack.config.js
└── webviews
    ├── components
    │   ├── AcceptRejectBar.svelte
    │   ├── ChatWebview.svelte
    │   ├── LogsWebview.svelte
    │   ├── OmniBar.svelte
    │   ├── chat
    │   │   ├── Chat.svelte
    │   │   ├── Response.svelte
    │   │   ├── UserInput.svelte
    │   │   └── dropdown
    │   │       ├── Dropdown.svelte
    │   │       └── DropdownCard.svelte
    │   ├── icons
    │   │   ├── AcceptRejectCheck.svelte
    │   │   ├── AcceptRejectClose.svelte
    │   │   ├── ArrowDownSvg.svelte
    │   │   ├── ArrowRightSvg.svelte
    │   │   ├── ChatSvg.svelte
    │   │   ├── CopySvg.svelte
    │   │   ├── EllipsisDarkSvg.svelte
    │   │   ├── EllipsisSvg.svelte
    │   │   ├── LogGreenSvg.svelte
    │   │   ├── LogRedSvg.svelte
    │   │   ├── LogYellowSvg.svelte
    │   │   ├── ResetSvg.svelte
    │   │   ├── RiftSvg.svelte
    │   │   ├── SendSvg.svelte
    │   │   ├── UserSvg.svelte
    │   │   ├── copySvg.js
    │   │   ├── oldUserSvg.svelte
    │   │   └── vscode-icon.svg
    │   ├── logs
    │   │   ├── Agent.svelte
    │   │   ├── Log.svelte
    │   │   └── Logs.svelte
    │   └── stores.ts
    ├── globals.d.ts
    ├── pages
    │   ├── Chat.ts
    │   └── Logs.ts
    └── tsconfig.json

18 directories, 68 files

```
