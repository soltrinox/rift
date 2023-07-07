<script lang='ts'>
  import {state} from '../../stores'
  import RiftSvg from "../../icons/RiftSvg.svelte"

  export let id:string
  export let focused:boolean = false

  const description = (id in $state.agents) ? $state.agents[id].description : 'code while you sleep'

</script>


<div class={`flex flex-col hover:cursor-pointer ${focused ? 'bg-[var(--vscode-quickInputList-focusBackground)]' : 'hover:bg-[var(--vscode-list-hoverBackground)]'}`}>
  <div class="flex flex-row">
    <RiftSvg />
    /{id}
  </div>
  <div class="text-[var(--vscode-gitDecoration-ignoredResourceForeground)]">
  {description}
  </div>
</div>