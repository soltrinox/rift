<script lang="ts">
    import LogGreenSvg from "../icons/LogGreenSvg.svelte";
    import LogYellow from "../icons/LogYellowSvg.svelte";
    import LogRed from "../icons/LogRedSvg.svelte";
    import ArrowRightSvg from "../icons/ArrowRightSvg.svelte";
    import ArrowDownSvg from "../icons/ArrowDownSvg.svelte";
    import ChatSvg from "../icons/ChatSvg.svelte";
    import EllipsisSvg from "../icons/EllipsisSvg.svelte";
    import Log from "./Log.svelte";
    // export let color = "green";
    export let title = "log this";
    export let done = false;
    export let color = "yellow";
    let expanded = false;
</script>

<div>
    <a class="flex select-none" on:click={() => (expanded = !expanded)}>
        {#if expanded == false}
            <div class="mx-1 mt-1.5">
                <ArrowRightSvg />
            </div>
        {:else}
            <div class="mx-1 mt-1.5">
                <ArrowDownSvg />
            </div>
        {/if}
        {#if done || color == "green"}
            <div class="mx-2 mt-0.5"><LogGreenSvg /></div>
        {:else if !done || color == "yellow"}
            <div class="mx-2 mt-0.5"><LogYellow /></div>
        {:else}
            <div class="mx-2 mt-0.5"><LogRed /></div>
        {/if}
        {title}
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
    <div hidden={!expanded}>
        <Log />
        <Log />
        <Log />
    </div>
</div>
