import { mergeAttributes, Node } from "@tiptap/core"
import type { Node as ProseMirrorNode } from "@tiptap/pm/model"
import { PluginKey } from "@tiptap/pm/state"

export type FileChipOptions = {
  HTMLAttributes: Record<string, any>
  renderLabel: (props: { options: FileChipOptions; node: ProseMirrorNode }) => string
}

export const FileChipPluginKey = new PluginKey("filechip")
export const FileChip = Node.create({
  name: "filechip",

  defaultOptions: {
    // default options
  },

  group: "inline",

  content: "inline*",

  parseHTML() {
    return [
      {
        tag: "filechip",
      },
    ]
  },

  renderHTML({ HTMLAttributes }) {
    return ["span", mergeAttributes({ class: 'text-red-400' }, HTMLAttributes), 0]
  },
})