<script lang="ts">
  import { onMount } from 'svelte';

  type WaitlistRequest = {
    id: string;
    email: string;
    full_name?: string;
    company?: string;
    created_at?: string;
  };

  let requests = $state<WaitlistRequest[]>([]);
  let loading = $state(false);
  let error = $state('');
  let selectedRequest = $state<WaitlistRequest | null>(null);
  let processingId = $state<string | null>(null);
  let emailSubject = $state('');
  let emailBody = $state('');

  async function fetchWaitlist() {
    loading = true;
    error = '';

    try {
      const response = await fetch('/api/v1/admin/waitlist', {
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Unable to load waitlist requests');
      }

      requests = await response.json();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Unknown error';
    } finally {
      loading = false;
    }
  }

  function openPreview(request: WaitlistRequest) {
    selectedRequest = request;
    emailSubject = `Your Convergio access is ready`;
    emailBody = [
      `Hello ${request.full_name ?? request.email},`,
      '',
      'Great news — your waitlist request has been approved.',
      'You can now sign in and start using Convergio.',
      '',
      'Best regards,',
      'Convergio Team'
    ].join('\n');
  }

  async function approveRequest() {
    if (!selectedRequest) return;

    processingId = selectedRequest.id;
    error = '';

    try {
      const response = await fetch(`/api/v1/admin/waitlist/${selectedRequest.id}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          email_subject: emailSubject,
          email_body: emailBody
        })
      });

      if (!response.ok) {
        throw new Error('Failed to approve request');
      }

      selectedRequest = null;
      await fetchWaitlist();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Approval failed';
    } finally {
      processingId = null;
    }
  }

  async function rejectRequest(requestId: string) {
    processingId = requestId;
    error = '';

    try {
      const response = await fetch(`/api/v1/admin/waitlist/${requestId}/reject`, {
        method: 'POST',
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Failed to reject request');
      }

      if (selectedRequest?.id === requestId) {
        selectedRequest = null;
      }

      await fetchWaitlist();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Rejection failed';
    } finally {
      processingId = null;
    }
  }

  onMount(fetchWaitlist);
</script>

<div class="space-y-4">
  <header>
    <h2 class="text-2xl font-semibold text-slate-900">Pending Waitlist Requests</h2>
    <p class="text-sm text-slate-600">Review and manage incoming access requests.</p>
  </header>

  <div class="flex justify-end">
    <button class="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white" onclick={fetchWaitlist}>
      Refresh
    </button>
  </div>

  {#if error}
    <p class="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p>
  {/if}

  {#if loading}
    <p class="text-sm text-slate-500">Loading waitlist requests...</p>
  {:else}
    <div class="overflow-x-auto rounded-lg border border-slate-200">
      <table class="min-w-full divide-y divide-slate-200 text-sm">
        <thead class="bg-slate-50">
          <tr>
            <th class="px-3 py-2 text-left font-medium text-slate-600">Email</th>
            <th class="px-3 py-2 text-left font-medium text-slate-600">Name</th>
            <th class="px-3 py-2 text-left font-medium text-slate-600">Company</th>
            <th class="px-3 py-2 text-left font-medium text-slate-600">Requested</th>
            <th class="px-3 py-2 text-left font-medium text-slate-600">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-200 bg-white">
          {#if requests.length === 0}
            <tr>
              <td class="px-3 py-6 text-center text-slate-500" colspan="5">No pending requests.</td>
            </tr>
          {:else}
            {#each requests as request}
              <tr>
                <td class="px-3 py-2 text-slate-800">{request.email}</td>
                <td class="px-3 py-2 text-slate-700">{request.full_name ?? '—'}</td>
                <td class="px-3 py-2 text-slate-700">{request.company ?? '—'}</td>
                <td class="px-3 py-2 text-slate-700">{request.created_at ?? '—'}</td>
                <td class="px-3 py-2">
                  <div class="flex gap-2">
                    <button
                      class="rounded-md bg-green-600 px-3 py-1 text-xs font-semibold text-white"
                      onclick={() => openPreview(request)}
                    >
                      Approve
                    </button>
                    <button
                      class="rounded-md bg-red-600 px-3 py-1 text-xs font-semibold text-white"
                      onclick={() => rejectRequest(request.id)}
                      disabled={processingId === request.id}
                    >
                      {processingId === request.id ? 'Rejecting...' : 'Reject'}
                    </button>
                  </div>
                </td>
              </tr>
            {/each}
          {/if}
        </tbody>
      </table>
    </div>
  {/if}

  {#if selectedRequest}
    <section class="space-y-3 rounded-lg border border-blue-200 bg-blue-50 p-4">
      <h3 class="text-lg font-semibold text-slate-900">Email Preview</h3>
      <p class="text-sm text-slate-700">Preview invite email before sending.</p>

      <label class="block text-sm font-medium text-slate-700" for="email-subject">Subject</label>
      <input
        id="email-subject"
        class="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
        bind:value={emailSubject}
      />

      <label class="block text-sm font-medium text-slate-700" for="email-body">Body</label>
      <textarea
        id="email-body"
        class="min-h-40 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
        bind:value={emailBody}
      ></textarea>

      <div class="flex gap-2">
        <button
          class="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white"
          onclick={approveRequest}
          disabled={processingId === selectedRequest.id}
        >
          {processingId === selectedRequest.id ? 'Sending...' : 'Send Approval Email'}
        </button>
        <button
          class="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700"
          onclick={() => {
            selectedRequest = null;
          }}
        >
          Cancel
        </button>
      </div>
    </section>
  {/if}
</div>
