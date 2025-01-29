<script lang="ts">
  interface Props {
    sources: Array<string>;
    onSourceClick: Function;
  }

  let { sources, onSourceClick }: Props = $props();
</script>

<h6 class="mb-0">Sourced from:</h6>
<ul>
  {#each sources as source}
    <li class="list-inline-item">
      <button
        type="button"
        class="btn btn-link py-0"
        onclick={() => {
          onSourceClick(source);
        }}
      >
        {source}
      </button>
    </li>
  {/each}
</ul>
