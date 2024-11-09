<script lang="ts">
  import { createEventDispatcher } from "svelte";

  import type { InputCommand } from "./appTypes";

  import { checkIfStringIsCommand, debounce } from "./utils";

  export let inputCommands: Array<InputCommand> = [];
  export let currentPrompt = "";
  export let isLoading = false;

  let showCommands = false;
  let inputReference = null;

  const dispatch = createEventDispatcher();

  function onKeydown(event: KeyboardEvent): void {
    const tabKeyWasNotPressed = event.key !== "Tab";

    if (tabKeyWasNotPressed || !showCommands) {
      return;
    }

    event.preventDefault();

    inputAutoCompleteCommand();
  }

  function inputAutoCompleteCommand(): void {
    for (const command of inputCommands) {
      if (command.label.includes(currentPrompt)) {
        currentPrompt = `${command.label} `;
        showCommands = false;
        break;
      }
    }
  }

  const onInputDebounced = debounce(onInput, 100);

  function onInput(event: InputEvent): void {
    showCommands = checkIfStringIsCommand(currentPrompt);

    for (const command of inputCommands) {
      if (currentPrompt.startsWith(command.label)) {
        showCommands = false;
        break;
      }
    }
  }

  function selectCommand(command: InputCommand): void {
    currentPrompt = `${command.label} `;
    showCommands = false;
    inputReference.focus();
  }

  function onSubmit(): void {
    dispatch("chatFormOnSubmit");
  }

  function onAddDocumentClick(): void {
    dispatch("chatFormOnAddDocumentClick");
  }
</script>

<form class="card" on:submit|preventDefault={onSubmit}>
  <div class="card-body">
    <div class="input-group">
      <input
        type="search"
        class="form-control"
        placeholder="Type '/' to see commands or enter a prompt, such as 'What is a cpu?'"
        required
        autofocus
        disabled={isLoading}
        bind:this={inputReference}
        bind:value={currentPrompt}
        on:keydown={onKeydown}
        on:input={onInputDebounced}
      />

      {#if showCommands}
        <ul class="command-list list-group">
          {#each inputCommands as command}
            <li
              class="list-group-item bg-dark text-white"
              on:click={() => selectCommand(command)}
            >
              <strong>{command.label}</strong>
              <small>{@html command.description}</small>
            </li>
          {/each}
        </ul>
      {/if}

      {#if isLoading}
        <button class="btn btn-outline-success" type="submit" disabled>
          <span class="spinner-border spinner-border-sm" aria-hidden="true"></span>
          Loading...
        </button>

        <button type="button" class="btn btn-outline-secondary" disabled>
          Add document
        </button>
      {:else}
        <button type="submit" class="btn btn-success">Send</button>

        <button
          type="button"
          class="btn btn-outline-dark"
          on:click={onAddDocumentClick}
        >
          Add document
        </button>
      {/if}
    </div>
  </div>
</form>

<style>
  .card {
    border-bottom-left-radius: 0;
    border-bottom-right-radius: 0;
  }

  .command-list {
    bottom: 55px;
    position: absolute;
  }

  .command-list li {
    cursor: pointer;
  }

  .command-list li:hover,
  .command-list li:focus {
    background-color: rgba(var(--bs-secondary-rgb), var(--bs-bg-opacity)) !important;
  }
</style>
