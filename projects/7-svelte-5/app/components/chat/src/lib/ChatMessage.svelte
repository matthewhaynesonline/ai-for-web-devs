<script lang="ts">
  import showdown from "showdown";

  import { ChatMessageRole, ChatMessageState } from "./appTypes";
  import type { ChatMessage } from "./appTypes";

  import ChatMessageSources from "./ChatMessageSources.svelte";
  import LoadingDots from "./LoadingDots.svelte";

  interface Props {
    chatMessage: ChatMessage;
    onSourceClick?: Function;
  }
  let { chatMessage, onSourceClick }: Props = $props();

  const showDownConverter = new showdown.Converter();

  let author = $derived.by(() => {
    let author = "🤖 MattGPT";

    if (chatMessage.role === ChatMessageRole.User) {
      author = "You";
    }

    return author;
  });

  let displayDate = $derived(new Date(chatMessage.created_at).toLocaleTimeString());

  let alertCssClass = $derived.by(() => {
    let alertCssClass = "alert-light";

    if (chatMessage.role === ChatMessageRole.User) {
      alertCssClass = "alert-primary";
    }

    return alertCssClass;
  });

  let chatMessageCssClass = $derived.by(() => {
    let chatMessageCssClass = "message--assistant";

    if (chatMessage.role === ChatMessageRole.User) {
      chatMessageCssClass = "message--user";
    }

    return chatMessageCssClass;
  });

  let rawMessage = $derived(chatMessage.content.split("SOURCES:")[0]);
  let processedMessageBody = $derived.by(() => {
    let processedMessageBody = "";

    if (rawMessage) {
      processedMessageBody = rawMessage.replace("Response:", "");
      processedMessageBody = showDownConverter.makeHtml(processedMessageBody);
    }

    return processedMessageBody;
  });

  let rawSources = $derived(chatMessage.content.split("SOURCES:")[1]);
  let sources = $derived.by(() => {
    let sources = [];

    if (rawSources) {
      sources = rawSources.split(",");
    }

    return sources;
  });
</script>

<div class="message-wrapper d-inline-block">
  <div class="alert {alertCssClass} message {chatMessageCssClass}">
    <h6 class="alert-heading">
      {author}
      <small class="text-body-secondary float-end">
        {displayDate}
      </small>
    </h6>

    {#if chatMessage.state === ChatMessageState.Pending}
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
