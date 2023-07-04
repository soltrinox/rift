<script lang="ts">
    import RiftSvg from "../icons/RiftSvg.svelte";
    export let message = "log this";
</script>

<div class="flex">
    <RiftSvg />
    {message}
</div>
