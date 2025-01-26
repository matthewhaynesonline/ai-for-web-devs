<script lang="ts">
  import showdown from "showdown";

  import type { ChatMessage } from "./appTypes";

  import ChatMessageSources from "./ChatMessageSources.svelte";
  import LoadingDots from "./LoadingDots.svelte";

  interface Props {
    message: ChatMessage;
    isUserMessageOverwrite?: boolean | null;
    isLoading?: boolean;
    onSourceClick?: Function;
  }

  let {
    message,
    isUserMessageOverwrite = null,
    isLoading = false,
    onSourceClick,
  }: Props = $props();

  if (isUserMessageOverwrite) {
    message.isUserMessage = isUserMessageOverwrite;
  }

  const showDownConverter = new showdown.Converter();

  let alertCssClass = $state("alert-primary");
  let messageCssClass = $state("message--user");

  if (!message.isUserMessage) {
    alertCssClass = "alert-light";
    messageCssClass = "message--app";
  }

  let rawMessage = $derived(message.content.split("SOURCES:")[0]);
  let processedMessageBody = $derived.by(() => {
    let processedMessageBody = "";

    if (rawMessage) {
      processedMessageBody = rawMessage.replace("Response:", "");
      processedMessageBody = showDownConverter.makeHtml(processedMessageBody);
    }

    return processedMessageBody;
  });

  let rawSources = $derived(message.content.split("SOURCES:")[1]);
  let sources = $derived.by(() => {
    let sources = [];

    if (rawSources) {
      sources = rawSources.split(",");
    }

    return sources;
  });
</script>

<div class="message-wrapper d-inline-block">
  <div class="alert {alertCssClass} message {messageCssClass}">
    <h6 class="alert-heading">
      {message.author}
      {#if message.date}
        <small class="text-body-secondary float-end">
          {new Date(message.date).toLocaleTimeString()}
        </small>
      {/if}
    </h6>

    {#if isLoading}
      <LoadingDots />
    {:else}
      {@html processedMessageBody}
    {/if}

    {#if sources?.length}
      <div class="mt-3">
        <ChatMessageSources {sources} {onSourceClick} />
      </div>
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
