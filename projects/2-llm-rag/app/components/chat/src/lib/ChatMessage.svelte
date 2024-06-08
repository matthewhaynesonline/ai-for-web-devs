<script lang="ts">
  import showdown from "showdown";

  import LoadingDots from "./LoadingDots.svelte";

  export let isLoading = false;
  export let isUserMessage = false;
  export let author;
  export let message;
  export let date;

  const showDownConverter = new showdown.Converter();

  let alertCssClass = "alert-primary";
  let messageCssClass = "message--user";

  if (!isUserMessage) {
    alertCssClass = "alert-light";
    messageCssClass = "message--app";
  }

  let processedMessage = "";

  $: if (message) {
    processedMessage = showDownConverter.makeHtml(message);
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

    {#if isLoading}
      <LoadingDots />
    {:else}
      {@html processedMessage}
    {/if}
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

  /* https://stackoverflow.com/a/59670838 */
  .message :global(p) {
    margin-bottom: 0;
  }
</style>
