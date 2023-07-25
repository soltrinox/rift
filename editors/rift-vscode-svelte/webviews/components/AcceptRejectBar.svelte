<script lang='ts'>
    import { stringify } from 'querystring';
    import Check from './icons/AcceptRejectCheck.svelte'
    import Close from './icons/AcceptRejectClose.svelte'
    import { state } from './stores';

    function handleAccept() {
        vscode.postMessage({type: "acceptOrReject", agentId: $state.selectedAgentId, doesAccept: true})
    }

    function handleReject() {
        vscode.postMessage({type: "acceptOrReject", agentId: $state.selectedAgentId, doesAccept: false})
    }

</script>

<div class="flex flex-row w-full bg-[var(--vscode-input-background)] p-1 px-2">
    <button on:click={handleAccept} class='flex bg-[#37662A] justify-center items-center flex-grow p-1 rounded-l-md'>Accept<Check/></button>
    <button on:click={handleReject} class='flex bg-[#763B22] justify-center items-center flex-grow p-1 rounded-r-md'>Reject<Close/></button>
</div>