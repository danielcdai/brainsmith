<script lang="ts">
    import UploadFile from '$lib/components/embedding/UploadFile.svelte';
</script>
    <div class="min-h-screen max-h-[100dvh] w-full flex justify-center">
    <div class=" flex flex-col justify-between w-full overflow-y-auto">
        <div class="max-w-2xl mx-auto w-full px-3 md:px-0 my-10">
            <div class="mb-6">
                <div class="justify-between items-center">
                    <div class="text-2xl font-semibold self-center py-2">
                        Enlighten me with your knowledge
                    </div>
                    <div class="text-xl font-semibold self-center py-2">
                        Choose a file
                    </div>
                </div>
                <UploadFile />
            </div>

        </div>
    </div>
</div>


