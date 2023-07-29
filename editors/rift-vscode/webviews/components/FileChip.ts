import { mergeAttributes, Node } from "@tiptap/core"
import type { Node as ProseMirrorNode } from "@tiptap/pm/model"
import { PluginKey } from "@tiptap/pm/state"

export type MentionOptions = {
  HTMLAttributes: Record<string, any>
  renderLabel: (props: { options: MentionOptions; node: ProseMirrorNode }) => string
}

export const MentionPluginKey = new PluginKey("mention")

export const Mention = Node.create<MentionOptions>({
  name: "mention",

  addOptions() {
    return {
      HTMLAttributes: {},
      renderLabel({ options, node }) {
        return `${node.attrs.label ?? node.attrs.id}`
      },
    }
  },

  group: "inline",

  inline: true,

  selectable: false,

  atom: true,

  addAttributes() {
    return {
      id: {
        default: null,
        parseHTML: (element) => element.getAttribute("data-id"),
        renderHTML: (attributes) => {
          if (!attributes.id) {
            return {}
          }

          return {
            "data-id": attributes.id,
          }
        },
      },

      label: {
        default: null,
        parseHTML: (element) => element.getAttribute("data-label"),
        renderHTML: (attributes) => {
          if (!attributes.label) {
            return {}
          }

          return {
            "data-label": attributes.label,
          }
        },
      },
    }
  },

  parseHTML() {
    return [
      {
        tag: `span[data-type="${this.name}"]`,
      },
    ]
  },

  renderHTML({ node, HTMLAttributes }) {
    return [
      "span",
      mergeAttributes({ "data-type": this.name }, this.options.HTMLAttributes, HTMLAttributes),
      this.options.renderLabel({
        options: this.options,
        node,
      }),
    ]
  },

  renderText({ node }) {
    return this.options.renderLabel({
      options: this.options,
      node,
    })
  },

  addKeyboardShortcuts() {
    return {
      Backspace: () =>
        this.editor.commands.command(({ tr, state }) => {
          let isMention = false
          const { selection } = state
          const { empty, anchor } = selection

          if (!empty) {
            return false
          }

          state.doc.nodesBetween(anchor - 1, anchor, (node, pos) => {
            if (node.type.name === this.name) {
              isMention = true
              tr.insertText("", pos, pos + node.nodeSize)

              return false
            }
          })

          return isMention
        }),
    }
  },

})
