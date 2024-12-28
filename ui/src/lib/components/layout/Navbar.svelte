<script lang="ts">
import Icon from "@iconify/svelte";
import Autocomplete from "@smui-extra/autocomplete";

let model = ['OPENAPI', 'OLLAMA'];

let valueOutlined: string | undefined = $state();
</script>

<div>
    <div>
        <button>
            <Icon icon="meteor-icons:xmark" width="24" height="24" />
        </button>
    </div>
    <div>
        <div>
            <Autocomplete
              options={model}
              textfield$variant="outlined"
              bind:value={valueOutlined}
              label="Outlined"
            />
        
            <pre class="status">Selected: {valueOutlined || ''}</pre>
          </div>
    </div>
</div>