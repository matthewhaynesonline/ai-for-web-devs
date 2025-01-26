<script lang="ts">
  import { run } from 'svelte/legacy';

  import { createEventDispatcher } from "svelte";
  import showdown from "showdown";

  import type { ChatMessage } from "./appTypes";

  import ChatMessageSources from "./ChatMessageSources.svelte";
  import LoadingDots from "./LoadingDots.svelte";

  interface Props {
    message: ChatMessage;
    isUserMessageOverwrite?: boolean | null;
    isLoading?: boolean;
  }

  let { message = $bindable(), isUserMessageOverwrite = null, isLoading = false }: Props = $props();

  if (isUserMessageOverwrite) {
    message.isUserMessage = isUserMessageOverwrite;
  }

  const dispatch = createEventDispatcher();
  const showDownConverter = new showdown.Converter();

  let alertCssClass = $state("alert-primary");
  let messageCssClass = $state("message--user");

  if (!message.isUserMessage) {
    alertCssClass = "alert-light";
    messageCssClass = "message--app";
  }

  let processedMessageBody = $state("");
  let sources: Array<string> = $state([]);

  run(() => {
    if (message.body) {
      const [rawMessage, rawSources] = message.body.split("SOURCES:");

      message.body = rawMessage.replace("Response:", "");
      processedMessageBody = showDownConverter.makeHtml(message.body);

      if (rawSources) {
        sources = rawSources.split(",");
      }
    }
  });

  function onSourceClick(event: Event): void {
    dispatch("chatMessageOnSourceClick", event.detail);
  }
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
        <ChatMessageSources
          {sources}
          on:chatMessageSourcesOnSourceClick={onSourceClick}
        />
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
