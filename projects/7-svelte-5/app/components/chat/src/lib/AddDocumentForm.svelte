<script lang="ts">
  interface Props {
    onSubmit: Function;
    onClose: Function;
  }

  let { onSubmit, onClose }: Props = $props();

  let title = $state("");
  let body = $state("");
</script>

<div class="modal d-inline-block">
  <form
    class="modal-dialog modal-dialog-centered"
    onsubmit={(event) => {
      event.preventDefault();
      onSubmit({
        title: title,
        body: body,
      });
    }}
  >
    <div class="modal-content">
      <div class="modal-header text-bg-dark">
        <h5 class="modal-title">Add a document to the model</h5>
        <button type="button" class="btn btn-dark fw-bolder" onclick={onClose}>
          ✕
        </button>
      </div>

      <div class="modal-body">
        <div class="mb-4">
          <label for="newDocumentTitle" class="form-label">
            <small>Title</small>
          </label>
          <input
            type="text"
            id="newDocumentTitle"
            class="form-control"
            placeholder="Enter a title, such as 'Cloud Computing'"
            required
            bind:value={title}
          />
        </div>

        <div class="mb-4">
          <label for="newDocumentBody" class="form-label">
            <small>Body</small>
          </label>
          <textarea
            class="form-control"
            id="newDocumentBody"
            placeholder="Enter body content, such as 'Cloud computing refers to...'"
            required
            rows="4"
            bind:value={body}
          ></textarea>
        </div>
      </div>

      <div class="modal-footer text-bg-light">
        <button type="submit" class="btn btn-success">Save Document</button>

        <button type="button" class="btn btn-secondary" onclick={onClose}>
          Cancel
        </button>
      </div>
    </div>
  </form>
</div>

<style>
  .modal {
    background: rgba(0, 0, 0, 0.5);
  }
</style>
