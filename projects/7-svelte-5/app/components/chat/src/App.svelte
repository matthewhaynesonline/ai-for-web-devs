<script lang="ts">
  import { onMount } from "svelte";

  import {
    ChatMessageState,
    ToastState,
    defaultChat,
    defaultChatMessage,
    defaultToastMessage,
    defaultSource,
    ChatMessageRole,
  } from "./lib/appTypes";

  import type { Chat, ToastMessage, Source, InputCommand } from "./lib/appTypes";

  import {
    checkIfStringIsCommand,
    doRequest,
    getFileNameWithoutExtensionAndTimeStamp,
    scrollToBottom,
    handleOnBeforeUnload,
  } from "./lib/utils";

  import AddDocumentForm from "./lib/AddDocumentForm.svelte";
  import ChatForm from "./lib/ChatForm.svelte";
  import ChatMessageComponent from "./lib/ChatMessage.svelte";
  import MessageSourceModal from "./lib/MessageSourceModal.svelte";
  import Toast from "./lib/Toast.svelte";

  interface Props {
    initialChatState: Chat;
  }
  let { initialChatState }: Props = $props();

  const inputCommands: InputCommand[] = [
    {
      label: "/image",
      description:
        "Generate an image. Type <strong>/image</strong> followed by a prompt.",
      endpoint: "/image-generate",
    },
  ];

  let aborter = new AbortController();

  let isLoading = $state(false);
  let showAddDocumentForm = $state(false);
  let showMessageSourceModal = $state(false);
  let showToast = $state(false);

  const defaultPrompt = "";
  let currentPrompt = $state(defaultPrompt);

  let chat = $state(structuredClone(initialChatState));
  let lastChatMessageIndex = $derived(chat.chat_messages.length - 1);

  let toastMessage: ToastMessage = $state(structuredClone(defaultToastMessage));
  let currentSource: Source = $state(structuredClone(defaultSource));

  /**
   * Utils
   */
  function refreshMessages(): void {
    scrollToBottom();
  }

  /**
   * Lifecycle
   */
  onMount(() => {
    refreshMessages();
  });

  /**
   * Chat
   */
  async function onChatFormSubmit(newPrompt: string): Promise<void> {
    currentPrompt = newPrompt;

    isLoading = true;
    aborter.abort();
    aborter = new AbortController();

    let newUserMessage = structuredClone(defaultChatMessage);
    newUserMessage.content = currentPrompt;
    chat.chat_messages.push(newUserMessage);

    let shouldRunCommand = checkIfStringIsCommand(currentPrompt);

    const requestBody = {
      prompt: currentPrompt,
    };

    currentPrompt = defaultPrompt;

    let newAssistantMessage = structuredClone(defaultChatMessage);
    newAssistantMessage.role = ChatMessageRole.Assistant;
    newAssistantMessage.state = ChatMessageState.Pending;
    chat.chat_messages.push(newAssistantMessage);

    refreshMessages();

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
            chat.chat_messages[lastChatMessageIndex].content += text;
          } else {
            chat.chat_messages[lastChatMessageIndex].state = ChatMessageState.Ready;
            chat.chat_messages[lastChatMessageIndex].content = text;
            chat.chat_messages[lastChatMessageIndex].created_at = new Date(
              Date.now(),
            ).toISOString();

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
    chat.chat_messages[lastChatMessageIndex].content = responseData.output;
    chat.chat_messages[lastChatMessageIndex].state = ChatMessageState.Ready;
    chat.chat_messages[lastChatMessageIndex].created_at = new Date(
      Date.now(),
    ).toISOString();
    refreshMessages();
  }

  async function onClearChat(event: Event): Promise<void> {
    if (!window.confirm("Are you sure you want to clear the chat?")) {
      return;
    }

    const endpointUrl = `/chats/${initialChatState.id}/chat-messages`;
    await doRequest(endpointUrl, {}, aborter, "DELETE");

    flashToast("Success!", "Chat cleared!", ToastState.Info);

    currentPrompt = defaultPrompt;
    chat = structuredClone(defaultChat);

    refreshMessages();
  }

  /**
   * Add Doc
   */
  function onChatAddDocumentClick(): void {
    showAddDocumentForm = true;
  }

  async function addDocumentFormSubmit(newDocument: object): Promise<void> {
    showAddDocumentForm = false;
    isLoading = true;

    const endpointUrl = "/document";

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

  /**
   * Message Source
   */
  async function onSourceClick(sourceName: string): Promise<void> {
    isLoading = true;

    sourceName = getFileNameWithoutExtensionAndTimeStamp(sourceName).trim();
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

  /**
   * Toast
   */
  async function flashToast(
    title = "There was an error.",
    content = "Please try again later.",
    state: ToastState = ToastState.Danger,
  ): Promise<void> {
    toastMessage.title = title;
    toastMessage.content = content;
    toastMessage.state = state;

    showToast = true;

    await new Promise((resolve) => setTimeout(resolve, 5000));

    showToast = false;
  }

  function onToastClose(): void {
    showToast = false;
    toastMessage = structuredClone(defaultToastMessage);
  }
</script>

<svelte:window onbeforeunload={(event) => handleOnBeforeUnload(event, isLoading)} />

<main class="pb-5">
  {#if showToast}
    <Toast {toastMessage} onClose={onToastClose} />
  {/if}

  {#if showAddDocumentForm}
    <AddDocumentForm
      onSubmit={addDocumentFormSubmit}
      onClose={onAddDocumentFormClose}
    />
  {/if}

  {#if showMessageSourceModal}
    <MessageSourceModal source={currentSource} onClose={onMessageSourceModalClose} />
  {/if}

  <div class="border-bottom border-dark-subtle mb-4 pb-3">
    <h5 class="d-inline-block mr-2">
      {initialChatState.title}
    </h5>
    <button
      type="button"
      class="btn btn-sm btn-outline-danger float-end"
      onclick={onClearChat}
    >
      Clear Chat
    </button>
  </div>

  <ul class="list-unstyled">
    {#each chat.chat_messages as chatMessage, i}
      <li>
        <ChatMessageComponent {chatMessage} {onSourceClick} />
      </li>
    {/each}
  </ul>

  <div class="fixed-bottom">
    <div class="container">
      <ChatForm
        {inputCommands}
        {currentPrompt}
        {isLoading}
        onSubmit={onChatFormSubmit}
        onAddDocumentClick={onChatAddDocumentClick}
      />
    </div>
  </div>
</main>
