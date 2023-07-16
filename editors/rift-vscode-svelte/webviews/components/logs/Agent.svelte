<script lang="ts">
    import LogGreenSvg from "../icons/LogGreenSvg.svelte";
    import LogYellow from "../icons/LogYellowSvg.svelte";
    import LogRed from "../icons/LogRedSvg.svelte";
    import ArrowRightSvg from "../icons/ArrowRightSvg.svelte";
    import ArrowDownSvg from "../icons/ArrowDownSvg.svelte";
    import ChatSvg from "../icons/ChatSvg.svelte";
    import EllipsisSvg from "../icons/EllipsisSvg.svelte";
    import EllipsisDarkSvg from "../icons/EllipsisDarkSvg.svelte";
    import Log from "./Log.svelte";
    import { state } from "../stores";
    import type { SvelteStore } from "../../../src/types";

    let expanded = false;
    export let id: string = "";
    export let selectedId = "";
    export let name: string = "rift_chat";
    export let hasChatNotification = false;
    export let hasInputNotification = false;

    $: isSelected = id == selectedId;

    let doneAgent = false;

    let isDropdownOpen = false; // default state (dropdown close)

    const handleDropdownClick = () => {
        isDropdownOpen = !isDropdownOpen; // togle state on click
    };

    const handleDropdownFocusLoss = ({
        relatedTarget,
        currentTarget,
    }: FocusEvent) => {
        // use "focusout" event to ensure that we can close the dropdown when clicking outside or when we leave the dropdown with the "Tab" button
        const ct = currentTarget as HTMLElement;

        if (relatedTarget instanceof HTMLElement && ct.contains(relatedTarget))
            return; // check if the new focus target doesn't present in the dropdown tree (exclude ul\li padding area because relatedTarget, in this case, will be null)
        isDropdownOpen = false;
    };

    const handleChatIconClick = (e: MouseEvent) => {
        hasChatNotification = false;
        hasInputNotification = false;
        state.update((state) => ({
            ...state,
            selectedAgentId: id,
            agents: {
                ...state.agents,
                [id]: {
                    ...state.agents[id],
                    hasChatNotification: false,
                    hasInputNotification: false,
                },
            },
        }));
        vscode.postMessage({ type: "selectedAgentId", selectedAgentId: id });

        console.log("This is the state - Logs");
        console.log($state);
    };

    const handleCancelAgent = (e: MouseEvent) => {
        vscode.postMessage({ type: "cancelAgent", id: id });
    };
</script>

<div class:bg-[var(--vscode-editor-hoverHighlightBackground)]={isSelected}>
    <div class="flex hover:bg-red">
        <div class="flex select-none">
            {#if expanded == false}
                <button
                    class="mx-1"
                    on:click={() => (expanded = !expanded)}
                    on:keydown={() => (expanded = !expanded)}
                >
                    <ArrowRightSvg />
                </button>
            {:else}
                <button
                    class="mx-1"
                    on:click={() => (expanded = !expanded)}
                    on:keydown={() => (expanded = !expanded)}
                >
                    <ArrowDownSvg />
                </button>
            {/if}
            <button class="flex w-full" on:click={handleChatIconClick}>
                {#if $state.agents[id].tasks?.task.status == "done"}
                    <div class="mx-1 mt-0.5"><LogGreenSvg /></div>
                {:else if $state.agents[id].tasks?.task.status == "running"}
                    <div class="mx-1 mt-0.5"><LogYellow /></div>
                {:else}
                    <div class="mx-1 mt-0.5"><LogRed /></div>
                {/if}
                <div>{name}</div>
            </button>
        </div>

        <button
            class="relative inline-flex w-fit mr-2 mt-1.5 ml-auto flex hover:text-[var(--vscode-list-hoverBackground)]"
            on:click={handleChatIconClick}
        >
            {#if hasChatNotification || hasInputNotification}
                <div
                    class="absolute bottom-auto left-auto right-0 top-0 z-10 inline-block -translate-y-1/2 translate-x-2/4 rotate-0 skew-x-0 skew-y-0 scale-x-50 scale-y-50 rounded-full bg-pink-700 p-2.5 text-xs"
                />
            {/if}
            <ChatSvg />
        </button>

        <div class="dropdown inline-flex left-auto flex">
            <div class="flex items-center">
                <div class="dropdown" on:focusout={handleDropdownFocusLoss}>
                    <button class="btn pt-3" on:click={handleDropdownClick}>
                        {#if isDropdownOpen}
                            <div class="px-2"><EllipsisDarkSvg /></div>
                        {:else}
                            <div class="px-2"><EllipsisSvg /></div>
                        {/if}
                    </button>

                    <ul
                        style="left: auto !important;
                        right: 0px !important;
                        opacity: 100;z-index: 99; background-color: var(--vscode-button-secondaryBackground);"
                        class="dropdown-content absolute menu shadow rounded-box"
                        style:visibility={isDropdownOpen ? "visible" : "hidden"}
                    >
                        <li class="list-item">
                            <button
                                class="btn px-2"
                                on:click={handleCancelAgent}>Cancel</button
                            >
                        </li>
                        <li class="list-item">
                            <button class="btn px-2">Delete</button>
                        </li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
    <div class="border-l ml-6 my-2 space-y-2" hidden={!expanded}>
        {#if $state.agents[id].tasks.subtasks.length > 0}
            {#each $state.agents[id].tasks.subtasks as subtask}
                <Log {subtask} />
            {/each}
        {/if}
    </div>
</div>

<style>
    .list-item:hover {
        background-color: var(--vscode-button-secondaryHoverBackground);
    }
</style>
