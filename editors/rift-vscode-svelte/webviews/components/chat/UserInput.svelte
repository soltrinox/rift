<script lang='ts'>
  import {loading, state} from '../stores'
  export let value:string = '';

  let textarea;

  const resize = () => {
    textarea.style.height = 'auto';
    textarea.style.height = `${textarea.scrollHeight}px`;
  };



  function handleKeyDown(e) {
    if (e.key === "Enter") { // 13 is the Enter key code
          e.preventDefault();  // Prevent default Enter key action
          if(e.shiftKey) {
            this.value = this.value + '\n'
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
            return
          }
          this.blur()
          loading.set(true)

          vscode.postMessage({
            type: 'message',
              messages: $state.history , // don't want to include what we just pushed :()
            message: this.value
          })

        }
    // logic to handle keydown event
  };
</script>

<div class='w-full text-md p-2 min-h-8 bg-[var(--vscode-input-background)] flex flex-row'>
  <textarea bind:this={textarea} class='w-full min-h-8 block outline-none focus:outline-none bg-transparent resize-none' placeholder='Ask questions and get answers about the current code window.' on:input={resize} on:keydown={handleKeyDown} value={value} />
</div>
