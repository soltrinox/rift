<script lang='ts'>
  import RiftSvg from "./icons/RiftSvg.svelte";
  import ResetSvg from "./icons/ResetSvg.svelte";
  import { state, DEFAULT_STATE } from "./stores";
  function resetChat() {
    // console.log("reseting state");
    // state.set(DEFAULT_STATE);
    // vscode.setState(DEFAULT_STATE);
    // we're no longer reseting the entire state when you hit this LMAO... just going to reset the chat history of the selectedAgent
    state.update(state => ({...state, agents: {...state.agents, [state.selectedAgentId]: {...state.agents[state.selectedAgentId], chatHistory: state.agents[state.selectedAgentId].chatHistory.slice(-1) }}})) // chop off everything but the last message
  }

  let displayName: string | undefined

  $: {
    if($state.selectedAgentId && Object.keys($state.agents).length) {
    // have to get display name from availableAgents array (which comes from calling list Agents btw)
    console.log($state)
    displayName = $state.availableAgents.find(availableAgent => availableAgent.agent_type == $state.agents[$state.selectedAgentId].type)?.display_name
    if(!displayName) {
      console.log('what the fuck')
      console.log($state)
    }
  }
  }

</script>

<!-- maybe -->
<div
  class={`top-0 w-full px-2 py-1 flex justify-between z-10  bg-[var(--vscode-input-background)] `}
>
  <div
    class="flex flex-row text-xl items-center text-[var(--vscode-icon-foreground)]"
  >
    <RiftSvg color="var(--vscode-icon-foreground)" />
    {displayName ?? ''}
  </div>
  <div class="justify-self-end flex-shrink-0">
    <button class="flex items-center flex-shrink" on:click={resetChat}>
      <ResetSvg />
    </button>
  </div>
</div>
