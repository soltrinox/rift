import { CommandProps, Editor, mergeAttributes, Node } from "@tiptap/core"
import type { ParseRule } from "@tiptap/pm/model"
// import type { Node as ProseMirrorNode } from "@tiptap/pm/model"
import { PluginKey } from "@tiptap/pm/state"
import {Heading} from '@tiptap/extension-heading'

export type FileChipOptions = {
  HTMLAttributes: Record<string, any>
  // renderLabel: (props: { options: FileChipOptions; node: ProseMirrorNode }) => string
}

export const FileChipPluginKey = new PluginKey("filechip")
export const FileChip = Heading.extend<FileChipOptions>({
  name: "span",

  parseHTML(this: {
    name: string
    options: {}
    storage: any
    parent: (() => readonly ParseRule[] | undefined) | undefined
    editor?: Editor | undefined
  }) {
    console.log("parseHTML called. this:", this)
    return [
      {
        tag: "span",
      },
    ]
  },

  renderHTML({ node, HTMLAttributes }) {
    console.log("renderHTML called. node:", node)
    console.log("HTMLAttributes: ", HTMLAttributes)
    return ["span", mergeAttributes(this.options.HTMLAttributes, HTMLAttributes), 0]
  },
})