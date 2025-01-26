<script lang="ts">
  import { createEventDispatcher } from "svelte";

  let { sources = [] } = $props();

  const dispatch = createEventDispatcher();

  function onSourceClick(sourceName: string): void {
    dispatch("chatMessageSourcesOnSourceClick", sourceName);
  }
</script>

<h6 class="mb-0">Sourced from:</h6>
<ul>
  {#each sources as source}
    <li class="list-inline-item">
      <button type="button" class="btn btn-link py-0" onclick={onSourceClick(source)}>
        {source}
      </button>
    </li>
  {/each}
</ul>
