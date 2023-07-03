<script>

  export let dataId = null;
  export let value = '';
  let textarea;

  const resize = () => {
    textarea.style.height = 'auto';
    textarea.style.height = `${textarea.scrollHeight}px`;
  };

  const handleKeyDown = (e) => {
    // logic to handle keydown event
  };
</script>

<div class='w-full text-md p-2 min-h-8 bg-[var(--vscode-input-background)] flex flex-row'>
  <textarea bind:this={textarea} data-id={dataId} class='w-full min-h-8 block outline-none focus:outline-none bg-transparent resize-none' placeholder='Ask questions and get answers about the current code window.' on:input={resize} value={value} />
</div>
