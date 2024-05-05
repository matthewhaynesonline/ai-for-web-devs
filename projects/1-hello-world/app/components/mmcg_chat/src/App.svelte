<script lang="ts">
  import { doRequest, throttle } from "./lib/utils";

  import ChatForm from "./lib/ChatForm.svelte";
  import ChatMessage from "./lib/ChatMessage.svelte";
  import Toast from "./lib/Toast.svelte";

  let aborter = new AbortController();

  const defaultChatMessage = {
    body: "",
    author: "🤖 MattGPT",
    date: Date.now(),
  };

  const defaultToastMessage = {
    title: "",
    body: "",
    state: "danger",
  };

  let toastMessage = structuredClone(defaultToastMessage);

  let isLoading = false;
  let showToast = false;
  let currentPrompt = "";
  let messages = [];

  async function onChatFormSubmit(event) {
    isLoading = true;

    aborter.abort();
    aborter = new AbortController();

    messages.push({
      prompt: { body: currentPrompt, author: "You", date: Date.now() },
    });

    const requestBody = {
      prompt: currentPrompt,
    };

    currentPrompt = "";

    refreshMessages();

    messages[messages.length - 1].output = structuredClone(defaultChatMessage);

    const response = await doRequest("/prompt", requestBody, aborter);

    if (response?.ok) {
      const responseData = await response.json();

      messages[messages.length - 1].output.body = responseData.output;
      messages[messages.length - 1].output.date = Date.now();

      refreshMessages();
    } else {
      flashToast();
    }

    isLoading = false;
  }

  function refreshMessages() {
    // force svelte re-render
    // https://svelte.dev/tutorial/updating-arrays-and-objects
    messages = messages;

    scrollToBottom();
  }

  function scrollToBottom() {
    const throttleMs = 200;
    const timeoutMs = 10;

    throttle(
      setTimeout(function () {
        window.scrollTo({
          top: document.body.scrollHeight,
          behavior: "smooth",
        });
      }, timeoutMs),
      throttleMs,
    );
  }

  async function flashToast(
    title = "There was an error.",
    body = "Please try again later.",
    state = "danger",
  ) {
    toastMessage.title = title;
    toastMessage.body = body;
    toastMessage.state = state;

    showToast = true;

    await new Promise((resolve) => setTimeout(resolve, 5000));

    showToast = false;
  }

  function hideToast() {
    showToast = false;
    toastMessage = structuredClone(defaultToastMessage);
  }

  function onToastClose() {
    hideToast();
  }
</script>

<main class="pb-5">
  {#if showToast}
    <Toast
      bind:title={toastMessage.title}
      bind:body={toastMessage.body}
      bind:state={toastMessage.state}
      on:toastOnClose={onToastClose}
    />
  {/if}

  <ul class="list-unstyled">
    {#each messages as message, i}
      <li>
        {#if message.prompt}
          <ChatMessage
            isUserMessage={true}
            author={message.prompt.author}
            message={message.prompt.body}
            date={message.prompt.date}
          />
        {/if}

        {#if message.output.body}
          <ChatMessage
            isUserMessage={false}
            author={message.output.author}
            message={message.output.body}
            date={message.output.date}
          />
        {:else}
          <ChatMessage
            isUserMessage={false}
            author={message.output.author}
            message={message.output.body}
            date={message.output.date}
            isLoading={true}
          />
        {/if}
      </li>
    {/each}
  </ul>

  <div class="fixed-bottom">
    <div class="container">
      <ChatForm
        bind:currentPrompt
        bind:isLoading
        on:chatFormOnSubmit={onChatFormSubmit}
      />
    </div>
  </div>
</main>
