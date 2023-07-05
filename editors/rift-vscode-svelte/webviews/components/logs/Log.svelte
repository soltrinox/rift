<script lang="ts">
    import LogGreenSvg from "../icons/LogGreenSvg.svelte";
    import LogYellow from "../icons/LogYellowSvg.svelte";
    import LogRed from "../icons/LogRedSvg.svelte";
    import ChatSvg from "../icons/ChatSvg.svelte";
    import EllipsisSvg from "../icons/EllipsisSvg.svelte";
    export let color = "green";
    export let message = "log this";
    export let notification = true;
</script>

<a class="flex select-none">
    <div class="ml-6 border-l-4" />
    {#if color == "green"}
        <div class="ml-4 mr-2 mt-0.5"><LogGreenSvg /></div>
    {:else if color == "yellow"}
        <div class="ml-4 mr-2 mt-0.5"><LogYellow /></div>
    {:else}
        <div class="ml-4 mr-2 mt-0.5"><LogRed /></div>
    {/if}
    {message}
    <div class="relative inline-flex w-fit mr-2 mt-1 ml-auto flex">
        <div
            class="absolute bottom-auto left-auto right-0 top-0 z-10 inline-block -translate-y-1/2 translate-x-2/4 rotate-0 skew-x-0 skew-y-0 scale-x-50 scale-y-50 rounded-full bg-pink-700 p-2.5 text-xs"
        />
        <ChatSvg />
    </div>
    <div class="mr-2 mt-3">
        <EllipsisSvg />
    </div>
</a>
