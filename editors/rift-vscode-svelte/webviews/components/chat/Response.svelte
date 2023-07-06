<script lang="ts">
  import { onMount } from 'svelte'
  import RiftSvg from '../icons/RiftSvg.svelte'
  import { copySvg } from '../icons/copySvg'
  export let hasSvg = false
  export let value = ''
  // export let isNew = false;
  import { loading } from '../stores'
  import CopySvg from '../icons/CopySvg.svelte'
  import { SvelteComponent } from 'svelte'
  let responseBlock: HTMLDivElement
  var converter = new showdown.Converter({
    omitExtraWLInCodeBlocks: true,
    simplifiedAutoLink: true,
    excludeTrailingPunctuationFromURLs: true,
    literalMidWordUnderscores: true,
    simpleLineBreaks: true,
  })

  function textToFormattedHTML(text: string) {
    const time = Date.now()
    function fixCodeBlocks(response: string) {
      // Use a regular expression to find all occurrences of the substring in the string
      const REGEX_CODEBLOCK = new RegExp('```', 'g')
      const matches = response.match(REGEX_CODEBLOCK)

      // Return the number of occurrences of the substring in the response, check if even
      const count = matches ? matches.length : 0
      if (count % 2 === 0) {
        return response
      } else {
        // else append ``` to the end to make the last code block complete
        return response.concat('\n```')
      }
    }
    text = converter.makeHtml(fixCodeBlocks(text))
    console.log(`${Date.now() - time}ms latency`)
    return text
  }

  let something: string
  $: {
    const getHTML = (responseBlock: HTMLDivElement) => {
      responseBlock.innerHTML = textToFormattedHTML(value)
      responseBlock.querySelectorAll('code').forEach((node) => node.classList.add('code'))
      responseBlock.querySelectorAll('pre').forEach((preblock) => {
        preblock.classList.add('p-2', 'my-2', 'block', 'overflow-x-scroll')
        preblock.querySelectorAll('#copy').forEach((copy) => copy.parentElement?.removeChild(copy))
        const copyContent = value
        const copyButton = document.createElement('button')
        copyButton.id = 'copy'
        copyButton.className = 'flex text-sm py-1 mb-1 text-[var(--vscode-panelTitle-inactiveForeground)]'
        copyButton.appendChild(copySvg())
        const copyCodeWords = document.createElement('p')
        copyCodeWords.innerText = ' copy'
        copyButton.appendChild(copyCodeWords)
        copyButton.addEventListener('click', () => {
          // navigator.clipboard.writeText(copyContent)
          vscode.postMessage({ type: 'copyText', content: copyContent })
        })
        preblock.insertBefore(copyButton, preblock.firstChild)
      })
      return responseBlock.innerHTML
    }
    if (responseBlock) {
      const newHTML = getHTML(responseBlock)
      something = newHTML
      responseBlock.contentEditable = 'false'
    }
  }
</script>


<div class={`flex items-center pt-2 pl-2 ${value === '' && !loading ? 'hidden' : ''}`}>
  <RiftSvg size={12} />
  <p class="text-sm">RIFT</p>
</div>
<div class={`w-full text-md p-2 focus:outline-none min-h-8 flex flex-row ${value === '' && !loading ? 'hidden' : ''}`}>
  {#if hasSvg}
    <RiftSvg />
  {/if}
  <div
    contenteditable="true"
    bind:this={responseBlock}
    bind:innerHTML={something}
    id="response"
    class="w-full text-md min-h-8 focus:outline-none"
  />
</div>
