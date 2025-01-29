<script lang="ts">
  import { createEventDispatcher } from "svelte";
  import type { Source } from "./appTypes";

  interface Props {
    source: Source;
    onClose: Function;
  }

  let { source, onClose }: Props = $props();
</script>

<div class="modal d-inline-block">
  <div class="modal-dialog modal-dialog-centered">
    <div class="modal-content">
      <div class="modal-header text-bg-dark">
        <h5 class="modal-title">Source</h5>
        <button type="button" class="btn btn-dark fw-bolder" onclick={onClose}>
          ✕
        </button>
      </div>

      <div class="modal-body">
        <figure>
          <blockquote class="blockquote">
            <p>{source.page_content}</p>
          </blockquote>
          <figcaption class="blockquote-footer">
            <cite title="Source Title">{source.source}</cite>
          </figcaption>
        </figure>
      </div>
    </div>
  </div>
</div>

<style>
  .modal {
    background: rgba(0, 0, 0, 0.5);
  }
</style>
