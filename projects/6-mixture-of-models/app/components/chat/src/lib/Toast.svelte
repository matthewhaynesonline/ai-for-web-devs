<script lang="ts">
  import { createEventDispatcher } from "svelte";

  import type { ToastMessage } from "./appTypes";

  export let toastMessage: ToastMessage;

  const dispatch = createEventDispatcher();

  function onClose(): void {
    dispatch("toastOnClose");
  }
</script>

<div class="toast show" role="alert">
  <div class="toast-header text-bg-{toastMessage.state}">
    <strong class="me-auto">{toastMessage.title}</strong>
    <button type="button" class="btn-close" aria-label="Close" on:click={onClose}>
    </button>
  </div>

  <div class="toast-body">
    {toastMessage.body}
  </div>
</div>

<style>
  .toast {
    position: fixed;
    top: 2vh;
    right: 2vh;
    z-index: 9999;
    background-color: rgba(255, 255, 255, 0.95);
  }
</style>
