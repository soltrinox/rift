<script lang="ts">
    import LogGreenSvg from "../icons/LogGreenSvg.svelte";
    import LogYellow from "../icons/LogYellowSvg.svelte";
    import LogRed from "../icons/LogRedSvg.svelte";
    import ArrowRightSvg from "../icons/ArrowRightSvg.svelte";
    import ArrowDownSvg from "../icons/ArrowDownSvg.svelte";
    import ChatSvg from "../icons/ChatSvg.svelte";
    import EllipsisSvg from "../icons/EllipsisSvg.svelte";
    import EllipsisDarkSvg from "../icons/EllipsisDarkSvg.svelte";
    import OmniBar from "../chat/OmniBar.svelte";
    import Log from "./Log.svelte";
    import { loading, state } from "../stores";
    import { custom_event } from "svelte/internal";
    import { SvelteStore } from "../../../src/types";

    let expanded = false;
    export let id: string = "";
    export let name: string = "rift-chat";

    let doneAgent = false;
    let hasNotification = false;

    let isDropdownOpen = false; // default state (dropdown close)

    let store: SvelteStore;
    const unsubscribe = state.subscribe((s) => {
        store = s;
    });

    function handleMessage(
        event: CustomEvent<{
            id: string;
            hasNotification: boolean;
            done: boolean;
        }>
    ) {
        if (id == event.detail.id) {
            if (event.detail.done) {
                doneAgent = true;
            }
            if (event.detail.hasNotification) {
                hasNotification = true;
            }
        }
    }

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
        //     const omnibar = document.getElementById(
        //         "omnibar"
        //     ) as HTMLTextAreaElement;
        //     omnibar?.focus();
        //     omnibar.value = "/rift-chat";
        //     hasNotification = false;
        //     $state.agents[id].logs.splice(0);
    };
</script>

<div>
    <div
        class="flex"
        on:click={() => (expanded = !expanded)}
        on:keydown={() => (expanded = !expanded)}
    >
        <div
            class="flex select-none hover:text-[var(--vscode-list-hoverBackground)]"
        >
            {#if expanded == false}
                <div class="mx-1 mt-1.5">
                    <ArrowRightSvg />
                </div>
            {:else}
                <div class="mx-1 mt-1.5">
                    <ArrowDownSvg />
                </div>
            {/if}
            {#if doneAgent}
                <div class="mx-2 mt-0.5"><LogGreenSvg /></div>
            {:else}
                <div class="mx-2 mt-0.5"><LogYellow /></div>
                <!-- {:else}
                <div class="mx-2 mt-0.5"><LogRed /></div> -->
            {/if}
            <span>{name}</span>
        </div>

        <button
            class="relative inline-flex w-fit mr-2 mt-1.5 ml-auto flex"
            on:click={handleChatIconClick}
        >
            {#if hasNotification}
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
                            <button class="btn px-2">Cancel</button>
                        </li>
                        <li class="list-item">
                            <button class="btn px-2">Delete</button>
                        </li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
    <div hidden={!expanded}>
        {#if store.agents[id].tasks.subtasks.length > 0}
            {#each store.agents[id].tasks.subtasks as subtask}
                <Log {subtask} on:message={handleMessage} />
            {/each}
        {/if}
    </div>
</div>

<style>
    .list-item:hover {
        background-color: var(--vscode-button-secondaryHoverBackground);
    }
</style>
