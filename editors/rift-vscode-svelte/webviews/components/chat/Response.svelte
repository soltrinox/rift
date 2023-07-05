<script lang="ts">
  import { onMount } from "svelte"
  import RiftSvg from "../icons/RiftSvg.svelte";
  export let hasSvg = false;
  export let value = "";
  // export let isNew = false;
  import { loading } from "../stores";
  import CopySvg from "../icons/CopySvg.svelte"
  import { SvelteComponent } from "svelte";

  $: console.log($loading);
  $: console.log('value change')
  // $: console.log(value)
  $: {
    console.log(value)
    console.log('value chnge ^')
  }
  let responseBlock: HTMLDivElement
  var converter = new showdown.Converter({
    omitExtraWLInCodeBlocks: true, 
    simplifiedAutoLink: true,
    excludeTrailingPunctuationFromURLs: true,
    literalMidWordUnderscores: true,
    simpleLineBreaks: true
  });



  function textToFormattedHTML(text: string) {
    function fixCodeBlocks(response: string) {
    // Use a regular expression to find all occurrences of the substring in the string
    const REGEX_CODEBLOCK = new RegExp('\`\`\`', 'g');
    const matches = response.match(REGEX_CODEBLOCK);
  
    // Return the number of occurrences of the substring in the response, check if even
    const count = matches ? matches.length : 0;
    if (count % 2 === 0) {
      return response;
    } else {
      // else append ``` to the end to make the last code block complete
      return response.concat('\n\`\`\`');
    }
  }
    text = converter.makeHtml(fixCodeBlocks(text))
    return text
  }

    // responseBlock.contentEditable = 'true'
    // responseBlock.innerHTML = textToFormattedHTML(value)
    // responseBlock.contentEditable = 'false'
let something: string;
$: {
  if(responseBlock) responseBlock.contentEditable = 'true'
  something = textToFormattedHTML(value);
  if(responseBlock) responseBlock.contentEditable = 'false'
  const microlightReset = (responseBlock: HTMLDivElement) => {
    responseBlock.querySelectorAll('code').forEach(node => node.classList.add('code'))
    responseBlock.querySelectorAll('pre').forEach(preblock => {
      preblock.classList.add(
      "p-2",
      "my-2",
      "block",
      "overflow-x-scroll"
    )
    preblock.querySelectorAll('#copy').forEach(copy => copy.parentElement?.removeChild(copy))
    const copyContent = value
    const copyButton = document.createElement('button')
    copyButton.id = 'copy'
    copyButton.className = 'flex text-sm py-1 mb-1 text-[var(--vscode-panelTitle-inactiveForeground)]'
    const copySvgComponent = new CopySvg({
    target: copyButton,
    // pass any props here if CopySvg has any
    props: {}
});

    // copyButton.appendChild(copySvgComponent)

    const copyCodeWords = document.createElement('p')
    copyCodeWords.innerText = ' copy'
    copyButton.appendChild(copyCodeWords)
    copyButton.addEventListener('click', () => {
      // navigator.clipboard.writeText(copyContent)
      vscode.postMessage({type: 'copyText', content: copyContent})
    })
    preblock.insertBefore(copyButton, preblock.firstChild)
    microlight.reset('code')
  })
  }
  if(responseBlock) microlightReset(responseBlock)
}
</script>

<div class={`w-full text-md p-2 focus:outline-none min-h-8 flex flex-row ${(value === '' && !loading) ? 'hidden' : ''}`}>
  {#if hasSvg}
    <RiftSvg />
  {/if}
  <div 
  contenteditable='true' 
  bind:this={responseBlock}
  bind:innerHTML={something} 
  id="response" 
  class="w-full text-md min-h-8 focus:outline-none" >
  </div>
</div>
