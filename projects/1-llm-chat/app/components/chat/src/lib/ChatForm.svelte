<script lang="ts">
  import { createEventDispatcher } from "svelte";

  export let currentPrompt = "";
  export let isLoading = false;

  const dispatch = createEventDispatcher();

  function onSubmit() {
    dispatch("chatFormOnSubmit");
  }
</script>

<form class="card" on:submit|preventDefault={onSubmit}>
  <div class="card-body">
    <div class="input-group">
      <input
        type="search"
        class="form-control"
        placeholder="Enter a prompt, such as 'What is a cpu?'"
        required
        bind:value={currentPrompt}
      />

      {#if isLoading}
        <button class="btn btn-outline-success" type="submit" disabled>
          <span class="spinner-border spinner-border-sm" aria-hidden="true"></span>
          Loading...
        </button>
      {:else}
        <button type="submit" class="btn btn-success">Send</button>
      {/if}
    </div>
  </div>
</form>

<style>
  .card {
    border-bottom-left-radius: 0;
    border-bottom-right-radius: 0;
  }
</style>
