import { mergeAttributes, Node } from "@tiptap/core"
import type { Node as ProseMirrorNode } from "@tiptap/pm/model"
import { PluginKey } from "@tiptap/pm/state"

export type FileChipOptions = {
  HTMLAttributes: Record<string, any>
  renderLabel: (props: { options: FileChipOptions; node: ProseMirrorNode }) => string
}

export const FileChipPluginKey = new PluginKey("filechip")
const FileChip = Node.create({
  name: "filechip",

  defaultOptions: {
    // default options
  },

  group: "inline",

  content: "inline*",

  parseHTML() {
    return [
      {
        tag: "my-custom-node",
      },
    ]
  },

  renderHTML({ HTMLAttributes }) {
    return ["my-custom-node", HTMLAttributes, 0]
  },
})