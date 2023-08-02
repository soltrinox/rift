import { mergeAttributes, Node } from "@tiptap/core"
import Mention, { MentionOptions } from "@tiptap/extension-mention"
import { PluginKey } from "@tiptap/pm/state"
import Suggestion, { SuggestionOptions } from "@tiptap/suggestion"


export const MentionPluginKey = new PluginKey("filechip")

// type MentionOptions = {
//   HTMLAttributes: Record<string, any>
//   renderLabel: (props: { options: MentionOptions; node: ProseMirrorNode }) => string
//   suggestion: Omit<SuggestionOptions, "editor">
// }


//derived from mention Options
type FileChipOptions = {
    HTMLAttributes: Record<string, any>
    suggestion: Omit<SuggestionOptions, "editor">
}

export const FileChip = Node.create<FileChipOptions>({
  name: "filechip",

  addOptions() {
    return {
      HTMLAttributes: {},
      suggestion: {
        char: "@",
        pluginKey: MentionPluginKey,
        command: ({ editor, range, props }) => {
          // increase range.to by one when the next node is of type "text"
          // and starts with a space character
          const nodeAfter = editor.view.state.selection.$to.nodeAfter
          const overrideSpace = nodeAfter?.text?.startsWith(" ")

          if (overrideSpace) {
            range.to += 1
          }

          editor
            .chain()
            .focus()
            .insertContentAt(range, [
              {
                type: this.name,
                attrs: props,
              },
              {
                type: "text",
                text: " ",
              },
            ])
            .run()

          window.getSelection()?.collapseToEnd()
        },
        allow: ({ state, range }) => {
          const $from = state.doc.resolve(range.from)
          const type = state.schema.nodes[this.name]
          const allow = !!$from.parent.type.contentMatch.matchType(type)

          return allow
        },
      },
    }
  },

  group: "inline",

  inline: true,

  selectable: false,

  atom: true,

  addAttributes() {
    return {
      fileName: {
        default: null,
        parseHTML: (element) => element.getAttribute("data-filename"),
        renderHTML: (attributes) => {
            console.log('renderHTML function for fileName')
          if (!attributes.fileName) {
            return {}
          }

          return {
            "data-filename": attributes.fileName,
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

    function createFileSvg() {
      const xmlns = "http://www.w3.org/2000/svg"

      let svg = document.createElementNS(xmlns, "svg")
      svg.setAttribute("width", "10")
      svg.setAttribute("height", "10")
      svg.setAttribute("viewBox", "0 0 10 10")
      svg.setAttribute("fill", "none")
      svg.setAttribute("xmlns", xmlns)

      let g = document.createElementNS(xmlns, "g")
      g.setAttribute("clip-path", "url(#clip0_511_33161)")
      svg.appendChild(g)

      let path = document.createElementNS(xmlns, "path")
      path.setAttribute(
        "d",
        "M1.4248 1.22499C1.4248 1.0084 1.51085 0.800676 1.664 0.647521C1.81716 0.494367 2.02488 0.408325 2.24147 0.408325H6.31745C6.53403 0.408371 6.74172 0.494443 6.89484 0.647609L8.53552 2.28829C8.68869 2.44141 8.77476 2.6491 8.7748 2.86568V8.57499C8.7748 8.79158 8.68876 8.99931 8.53561 9.15246C8.38245 9.30562 8.17473 9.39166 7.95814 9.39166H2.24147C2.02488 9.39166 1.81716 9.30562 1.664 9.15246C1.51085 8.99931 1.4248 8.79158 1.4248 8.57499V1.22499ZM2.24147 1.02083C2.18732 1.02083 2.13539 1.04234 2.0971 1.08062C2.05882 1.11891 2.0373 1.17084 2.0373 1.22499V8.57499C2.0373 8.62914 2.05882 8.68107 2.0971 8.71936C2.13539 8.75765 2.18732 8.77916 2.24147 8.77916H7.95814C8.01229 8.77916 8.06422 8.75765 8.10251 8.71936C8.14079 8.68107 8.1623 8.62914 8.1623 8.57499V3.47083H6.52897C6.31238 3.47083 6.10466 3.38478 5.9515 3.23163C5.79835 3.07847 5.7123 2.87075 5.7123 2.65416V1.02083H2.24147ZM6.3248 1.02083V2.65416C6.3248 2.70831 6.34631 2.76024 6.3846 2.79853C6.42289 2.83681 6.47482 2.85833 6.52897 2.85833H8.1623C8.16051 2.8067 8.1392 2.75767 8.10269 2.72113L6.462 1.08044C6.42546 1.04393 6.37643 1.02262 6.3248 1.02083Z"
      )
      path.setAttribute("fill", "#CCCCCC")
      g.appendChild(path)

      let defs = document.createElementNS(xmlns, "defs")
      svg.appendChild(defs)

      let clipPath = document.createElementNS(xmlns, "clipPath")
      clipPath.setAttribute("id", "clip0_511_33161")
      defs.appendChild(clipPath)

      let rect = document.createElementNS(xmlns, "rect")
      rect.setAttribute("width", "9.8")
      rect.setAttribute("height", "9.8")
      rect.setAttribute("fill", "white")
      rect.setAttribute("transform", "translate(0.200195)")
      clipPath.appendChild(rect)

      return svg
    }
    const span = document.createElement("span")
    const attributesMap = mergeAttributes(this.options.HTMLAttributes, HTMLAttributes)
    for (let attribute in attributesMap) {
        span.setAttribute(attribute, attributesMap[attribute])
    }
    span.classList.add('bg-[var(--vscode-editor-background)]', 'text-xs', 'inline-flex', 'items-center', 'h-[1.5rem]')
    span.append(createFileSvg())
    span.append(document.createTextNode(`${node.attrs.fileName}`))

    console.log('rendering HTML:', span)
    return span

    // would prefer to use the nice prosemirror syntax, but prosemirror starts crying whenever you use SVG's (because capitalize attributes (I know ( stupid right we should fork prosemirror)))
  },

  renderText({ node }) {
    console.log('rendering text', node)
    return `[uri](${node.attrs.fsPath})`
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
              tr.insertText(this.options.suggestion.char || "", pos, pos + node.nodeSize)

              return false
            }
          })

          return isMention
        }),
    }
  },

  addProseMirrorPlugins() {
    return [
      Suggestion({
        editor: this.editor,
        ...this.options.suggestion,
      }),
    ]
  },
})


/*

  renderHTML({ node, HTMLAttributes }) {
    console.log("renderHTML called. node:", node)
    console.log("HTMLAttributes: ", HTMLAttributes)

    const svgString = `<svg width="10" height="10" viewBox="0 0 10 10" fill="none" xmlns="http://www.w3.org/2000/svg"><g clip-path="url(#clip0_511_33161)"><path d="M1.4248 1.22499C1.4248 1.0084 1.51085 0.800676 1.664 0.647521C1.81716 0.494367 2.02488 0.408325 2.24147 0.408325H6.31745C6.53403 0.408371 6.74172 0.494443 6.89484 0.647609L8.53552 2.28829C8.68869 2.44141 8.77476 2.6491 8.7748 2.86568V8.57499C8.7748 8.79158 8.68876 8.99931 8.53561 9.15246C8.38245 9.30562 8.17473 9.39166 7.95814 9.39166H2.24147C2.02488 9.39166 1.81716 9.30562 1.664 9.15246C1.51085 8.99931 1.4248 8.79158 1.4248 8.57499V1.22499ZM2.24147 1.02083C2.18732 1.02083 2.13539 1.04234 2.0971 1.08062C2.05882 1.11891 2.0373 1.17084 2.0373 1.22499V8.57499C2.0373 8.62914 2.05882 8.68107 2.0971 8.71936C2.13539 8.75765 2.18732 8.77916 2.24147 8.77916H7.95814C8.01229 8.77916 8.06422 8.75765 8.10251 8.71936C8.14079 8.68107 8.1623 8.62914 8.1623 8.57499V3.47083H6.52897C6.31238 3.47083 6.10466 3.38478 5.9515 3.23163C5.79835 3.07847 5.7123 2.87075 5.7123 2.65416V1.02083H2.24147ZM6.3248 1.02083V2.65416C6.3248 2.70831 6.34631 2.76024 6.3846 2.79853C6.42289 2.83681 6.47482 2.85833 6.52897 2.85833H8.1623C8.16051 2.8067 8.1392 2.75767 8.10269 2.72113L6.462 1.08044C6.42546 1.04393 6.37643 1.02262 6.3248 1.02083Z" fill="#CCCCCC"/></g><defs><clipPath id="clip0_511_33161"><rect width="9.8" height="9.8" fill="white" transform="translate(0.200195)"/></clipPath></defs></svg>`
    function createFileSvg() {
      const xmlns = "http://www.w3.org/2000/svg"

      let svg = document.createElementNS(xmlns, "svg")
      svg.setAttribute("width", "10")
      svg.setAttribute("height", "10")
      svg.setAttribute("viewBox", "0 0 10 10")
      svg.setAttribute("fill", "none")
      svg.setAttribute("xmlns", xmlns)

      let g = document.createElementNS(xmlns, "g")
      g.setAttribute("clip-path", "url(#clip0_511_33161)")
      svg.appendChild(g)

      let path = document.createElementNS(xmlns, "path")
      path.setAttribute(
        "d",
        "M1.4248 1.22499C1.4248 1.0084 1.51085 0.800676 1.664 0.647521C1.81716 0.494367 2.02488 0.408325 2.24147 0.408325H6.31745C6.53403 0.408371 6.74172 0.494443 6.89484 0.647609L8.53552 2.28829C8.68869 2.44141 8.77476 2.6491 8.7748 2.86568V8.57499C8.7748 8.79158 8.68876 8.99931 8.53561 9.15246C8.38245 9.30562 8.17473 9.39166 7.95814 9.39166H2.24147C2.02488 9.39166 1.81716 9.30562 1.664 9.15246C1.51085 8.99931 1.4248 8.79158 1.4248 8.57499V1.22499ZM2.24147 1.02083C2.18732 1.02083 2.13539 1.04234 2.0971 1.08062C2.05882 1.11891 2.0373 1.17084 2.0373 1.22499V8.57499C2.0373 8.62914 2.05882 8.68107 2.0971 8.71936C2.13539 8.75765 2.18732 8.77916 2.24147 8.77916H7.95814C8.01229 8.77916 8.06422 8.75765 8.10251 8.71936C8.14079 8.68107 8.1623 8.62914 8.1623 8.57499V3.47083H6.52897C6.31238 3.47083 6.10466 3.38478 5.9515 3.23163C5.79835 3.07847 5.7123 2.87075 5.7123 2.65416V1.02083H2.24147ZM6.3248 1.02083V2.65416C6.3248 2.70831 6.34631 2.76024 6.3846 2.79853C6.42289 2.83681 6.47482 2.85833 6.52897 2.85833H8.1623C8.16051 2.8067 8.1392 2.75767 8.10269 2.72113L6.462 1.08044C6.42546 1.04393 6.37643 1.02262 6.3248 1.02083Z"
      )
      path.setAttribute("fill", "#CCCCCC")
      g.appendChild(path)

      let defs = document.createElementNS(xmlns, "defs")
      svg.appendChild(defs)

      let clipPath = document.createElementNS(xmlns, "clipPath")
      clipPath.setAttribute("id", "clip0_511_33161")
      defs.appendChild(clipPath)

      let rect = document.createElementNS(xmlns, "rect")
      rect.setAttribute("width", "9.8")
      rect.setAttribute("height", "9.8")
      rect.setAttribute("fill", "white")
      rect.setAttribute("transform", "translate(0.200195)")
      clipPath.appendChild(rect)

      return svg
    }

    const span = document.createElement('span')
    const attributesMap = mergeAttributes(this.options.HTMLAttributes, HTMLAttributes)
    for (let attribute in attributesMap) {
      span.setAttribute(attribute, attributesMap[attribute])
    }
    span.append(createFileSvg())
    span.append(document.createTextNode(`${node.attrs.name}`))
    return span
  },
})
*/