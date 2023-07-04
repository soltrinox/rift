<script lang="ts">
  import { loading, state } from '../stores'
  export let value: string = ''
  export let enabled: boolean = false

  function resize(event: Event) {
    let targetElement = event.target as HTMLElement
    targetElement.style.height = 'auto'
    targetElement.style.height = `${targetElement.scrollHeight}px`
  }

  let textarea: HTMLTextAreaElement

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === 'Enter') {
      // 13 is the Enter key code
      e.preventDefault() // Prevent default Enter key action
      if (e.shiftKey) {
        textarea.value = textarea.value + '\n'
        textarea.style.height = 'auto'
        textarea.style.height = textarea.scrollHeight + 'px'
        return
      }
      textarea.blur()
      loading.set(true)

      vscode.postMessage({
        type: 'chatMessage',
        messages: $state.history, 
        message: textarea.value,
      })
      console.log('updating state...')
      state.update((state) => ({ ...state, history: [...state.history, { role: 'user', content: textarea.value }] }))
      textarea.value = ""
    }
    // logic to handle keydown event
  }
</script>

<div class="w-full text-md p-2 min-h-8 bg-[var(--vscode-input-background)] flex flex-row">
  <textarea
    bind:this={textarea}
    class="w-full min-h-8 block outline-none focus:outline-none bg-transparent resize-none"
    placeholder="Ask questions and get answers about the current code window."
    on:input={resize}
    on:keydown={handleKeyDown}
    disabled={!enabled}
    {value}
  />
</div>
