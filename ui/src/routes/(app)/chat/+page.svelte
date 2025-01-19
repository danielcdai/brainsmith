<script lang="ts">
    import MessageInput from "$lib/components/chat/MessageInput.svelte";
</script>

<div class="flex flex-col flex-auto h-full ">
    <div class="pb-2.5 flex flex-col flex-auto w-full h-0 justify-between">
        <div class="text-center text-2xl font-bold">
            Chat Box
        </div>
    </div>
    <div class="w-4/5 px-2.5 mx-auto inset-x-0">
        <MessageInput />
    </div>
    

</div>