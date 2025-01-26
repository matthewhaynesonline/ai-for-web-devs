<script lang="ts">
  import { onMount } from "svelte";

  import {
    BackendChatMessageRole,
    ChatMessageAuthor,
    ToastState,
  } from "./lib/appTypes";

  import type {
    InitialChatState,
    ChatMessage,
    ToastMessage,
    Source,
    InputCommand,
  } from "./lib/appTypes";

  import {
    checkIfStringIsCommand,
    doRequest,
    getFileNameWithoutExtensionAndTimeStamp,
    scrollToBottom,
  } from "./lib/utils";

  import AddDocumentForm from "./lib/AddDocumentForm.svelte";
  import ChatForm from "./lib/ChatForm.svelte";
  import ChatMessageComponent from "./lib/ChatMessage.svelte";
  import MessageSourceModal from "./lib/MessageSourceModal.svelte";
  import Toast from "./lib/Toast.svelte";

  export let initialChatState: InitialChatState;

  let aborter = new AbortController();

  let isLoading = false;
  let showAddDocumentForm = false;
  let showMessageSourceModal = false;
  let showToast = false;

  const inputCommands: InputCommand[] = [
    {
      label: "/image",
      description:
        "Generate an image. Type <strong>/image</strong> followed by a prompt.",
      endpoint: "/image-generate",
    },
  ];

  const defaultPrompt = "";
  let currentPrompt = defaultPrompt;

  const defaultMessages: Array<ChatMessage> = [];
  let messages = structuredClone(defaultMessages);

  const userAuthor = ChatMessageAuthor.User;
  const defaultChatMessage: ChatMessage = {
    body: "",
    author: ChatMessageAuthor.System,
    date: null,
    isUserMessage: false,
  };

  const defaultToastMessage: ToastMessage = {
    title: "",
    body: "",
    state: ToastState.Danger,
  };

  let toastMessage: ToastMessage = structuredClone(defaultToastMessage);

  let defaultSource: Source = {
    source: "",
    page_content: "",
  };

  let currentSource: Source = structuredClone(defaultSource);

  onMount(() => {
    setChatMessageFromInitialState();
  });

  function setChatMessageFromInitialState(): void {
    initialChatState?.chat_messages.forEach((message) => {
      let newMessage = structuredClone(defaultChatMessage);
      newMessage.body = message.content;
      newMessage.date = new Date(message.created_at);

      if (message.role === BackendChatMessageRole.User) {
        newMessage.author = userAuthor;
        newMessage.isUserMessage = true;
      }

      messages.push(newMessage);
    });

    refreshMessages();
  }

  function refreshMessages(): void {
    // force svelte re-render
    // https://svelte.dev/tutorial/updating-arrays-and-objects
    messages = messages;

    scrollToBottom();
  }

  async function onClearChat(event: Event): Promise<void> {
    if (!window.confirm("Are you sure you want to clear the chat?")) {
      return;
    }

    const endpointUrl = `/chats/${initialChatState.id}/chat-messages`;
    await doRequest(endpointUrl, {}, aborter, "DELETE");

    flashToast("Success!", "Chat cleared!", ToastState.Info);

    currentPrompt = defaultPrompt;
    messages = structuredClone(defaultMessages);

    refreshMessages();
  }

  async function flashToast(
    title = "There was an error.",
    body = "Please try again later.",
    state: ToastState = ToastState.Danger,
  ): Promise<void> {
    toastMessage.title = title;
    toastMessage.body = body;
    toastMessage.state = state;

    showToast = true;

    await new Promise((resolve) => setTimeout(resolve, 5000));

    showToast = false;
  }

  function onToastClose(): void {
    showToast = false;
    toastMessage = structuredClone(defaultToastMessage);
  }

  async function onChatFormSubmit(event: Event): Promise<void> {
    isLoading = true;

    aborter.abort();
    aborter = new AbortController();

    messages.push({
      body: currentPrompt,
      author: userAuthor,
      date: Date.now(),
      isUserMessage: true,
    });

    let shouldRunCommand = checkIfStringIsCommand(currentPrompt);

    const requestBody = {
      prompt: currentPrompt,
    };

    currentPrompt = defaultPrompt;

    refreshMessages();

    messages.push(structuredClone(defaultChatMessage));

    if (shouldRunCommand) {
      for (const command of inputCommands) {
        if (requestBody.prompt.startsWith(command.label)) {
          await doCommand(command, requestBody);
        }
      }
    } else {
      await promptStream(requestBody);
    }

    isLoading = false;
  }

  async function doCommand(command: InputCommand, requestBody: object) {
    requestBody.prompt = requestBody.prompt.replace(command.label, "");

    const response = await doRequest(command.endpoint, requestBody, aborter);

    if (response?.ok) {
      await addMessageFromResponse(response);
    } else {
      flashToast();
    }
  }

  async function promptStream(requestBody: object) {
    const response = await doRequest("/prompt-stream", requestBody, aborter);

    if (response?.ok) {
      const contentType = response.headers.get("content-type");
      const isJson = contentType?.includes("application/json");

      if (isJson) {
        await addMessageFromResponse(response);
      } else {
        let firstTokenLoadedAlreadyLoaded = false;
        const reader = response.body.getReader();

        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            break;
          }

          const text = new TextDecoder().decode(value);

          if (firstTokenLoadedAlreadyLoaded) {
            messages[messages.length - 1].body += text;
          } else {
            messages[messages.length - 1].body = text;
            messages[messages.length - 1].date = Date.now();

            firstTokenLoadedAlreadyLoaded = true;
          }

          refreshMessages();
        }
      }
    } else {
      flashToast();
    }
  }

  async function addMessageFromResponse(response) {
    const responseData = await response.json();
    messages[messages.length - 1].body = responseData.output;
    messages[messages.length - 1].date = Date.now();
    refreshMessages();
  }

  function onChatAddDocumentClick(): void {
    showAddDocumentForm = true;
  }

  async function addDocumentFormSubmit(event: Event): Promise<void> {
    showAddDocumentForm = false;
    isLoading = true;

    const endpointUrl = "/document";
    const newDocument = event.detail;

    aborter.abort();
    aborter = new AbortController();

    let response = await doRequest(endpointUrl, newDocument, aborter);

    if (response?.ok) {
      flashToast("Success!", "Document added successfully", ToastState.Success);
    } else {
      flashToast();
    }

    isLoading = false;
  }

  function onAddDocumentFormClose(): void {
    showAddDocumentForm = false;
  }

  async function onSourceClick(event: Event): Promise<void> {
    isLoading = true;

    let sourceName = getFileNameWithoutExtensionAndTimeStamp(event.detail).trim();

    currentSource = (await getSource(sourceName)) as Source;
    showMessageSourceModal = true;

    isLoading = false;
  }

  async function getSource(sourceName: string): Promise<object> {
    let source = null;

    const endpointUrl = "/document/find";

    aborter.abort();
    aborter = new AbortController();

    let response = await doRequest(`${endpointUrl}/${sourceName}`, {}, aborter, "GET");

    if (response?.ok) {
      source = await response.json();
    }

    return source;
  }

  function onMessageSourceModalClose(): void {
    showMessageSourceModal = false;
    currentSource = structuredClone(defaultSource);
  }
</script>

<main class="pb-5">
  {#if showToast}
    <Toast bind:toastMessage on:toastOnClose={onToastClose} />
  {/if}

  {#if showAddDocumentForm}
    <AddDocumentForm
      on:addDocumentFormOnSubmit={addDocumentFormSubmit}
      on:addDocumentFormOnClose={onAddDocumentFormClose}
    />
  {/if}

  {#if showMessageSourceModal}
    <MessageSourceModal
      source={currentSource}
      on:messageSourceModalOnClose={onMessageSourceModalClose}
    />
  {/if}

  <div class="border-bottom border-dark-subtle mb-4 pb-3">
    <h5 class="d-inline-block mr-2">
      {initialChatState.title}
    </h5>
    <button
      type="button"
      class="btn btn-sm btn-outline-danger float-end"
      on:click={onClearChat}
    >
      Clear Chat
    </button>
  </div>

  <ul class="list-unstyled">
    {#each messages as message, i}
      <li>
        {#if message.isUserMessage}
          <ChatMessageComponent {message} />
        {:else if message.body}
          <ChatMessageComponent {message} on:chatMessageOnSourceClick={onSourceClick} />
        {:else}
          <ChatMessageComponent
            {message}
            isUserMessageOverwrite={false}
            isLoading={true}
            on:chatMessageOnSourceClick={onSourceClick}
          />
        {/if}
      </li>
    {/each}
  </ul>

  <div class="fixed-bottom">
    <div class="container">
      <ChatForm
        {inputCommands}
        bind:currentPrompt
        bind:isLoading
        on:chatFormOnSubmit={onChatFormSubmit}
        on:chatFormOnAddDocumentClick={onChatAddDocumentClick}
      />
    </div>
  </div>
</main>
