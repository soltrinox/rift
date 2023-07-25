<script lang='ts'>
    import Check from './icons/AcceptRejectCheck.svelte'
    import Close from './icons/AcceptRejectClose.svelte'
</script>

<div class="flex flex-row w-full bg-[var(--vscode-input-background)] p-1 px-2">
    <button class='flex bg-[#37662A] justify-center items-center flex-grow p-1 rounded-l-md'>Accept<Check/></button>
    <button class='flex bg-[#763B22] justify-center items-center flex-grow p-1 rounded-r-md'>Reject<Close/></button>
</div>