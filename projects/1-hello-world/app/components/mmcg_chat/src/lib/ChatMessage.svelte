<script lang="ts">
  import LoadingDots from "./LoadingDots.svelte";

  export let isLoading = false;
  export let isUserMessage = false;
  export let author;
  export let message;
  export let date;

  let alertCssClass = "alert-primary";
  let messageCssClass = "message--user";

  if (!isUserMessage) {
    alertCssClass = "alert-light";
    messageCssClass = "message--app";
  }
</script>

<div class="message-wrapper d-inline-block">
  <div class="alert {alertCssClass} message {messageCssClass}">
    <h6 class="alert-heading">
      {author}
      <small class="text-body-secondary float-end">
        {new Date(date).toLocaleTimeString()}
      </small>
    </h6>

    <p class="mb-0">
      {#if isLoading}
        <LoadingDots />
      {:else}
        {message}
      {/if}
    </p>
  </div>
</div>

<style>
  .message-wrapper {
    width: 100%;
  }

  .message {
    width: 50%;
  }

  .message--user {
    float: right;
  }

  .message--app {
    float: left;
  }
</style>
