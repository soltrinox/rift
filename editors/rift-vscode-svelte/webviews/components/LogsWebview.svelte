<!-- Navbar.svelte -->
<script lang="ts">
    import EllipsisSvg from "./icons/EllipsisDarkSvg.svelte";
    import Logs from "./logs/Logs.svelte";
    import { DEFAULT_STATE, loading, state } from "./stores";
    import type { AgentRegistryItem } from "../../src/types";
    import Header from "./Header.svelte";
    import Chat from "./chat/Chat.svelte";
    import OmniBar from "./chat/OmniBar.svelte";
    import { onMount } from "svelte";
    import type {
        AgentChatRequest,
        AgentInputRequest,
        AgentResult,
        AgentUpdate,
        AgentProgress,
    } from "../../src/client";
    let agentRegistry: AgentRegistryItem[] = [];
</script>

<div class="">
    <div>
        <Logs />
    </div>
</div>
