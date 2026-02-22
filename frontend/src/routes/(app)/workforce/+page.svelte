<script lang="ts">
import { onMount } from 'svelte';

type MemberType = 'human' | 'agent';
type MemberStatus = 'active' | 'invited' | 'offline';

interface TeamMember {
id: string;
name: string;
type: MemberType;
role: string;
status: MemberStatus;
capabilities: string[];
}

let loading = $state(true);
let error: string | null = $state(null);
let teamMembers = $state<TeamMember[]>([]);
let teamId = $state('');

const statusStyles: Record<MemberStatus, string> = {
active: 'bg-green-100 text-green-700',
invited: 'bg-amber-100 text-amber-700',
offline: 'bg-surface-100 text-surface-700'
};

function normalizeType(value: unknown): MemberType {
return String(value ?? '')
.trim()
.toLowerCase() === 'agent'
? 'agent'
: 'human';
}

function normalizeStatus(value: unknown): MemberStatus {
const normalized = String(value ?? '')
.trim()
.toLowerCase();

if (normalized === 'invited' || normalized === 'pending') return 'invited';
if (normalized === 'offline' || normalized === 'inactive') return 'offline';
return 'active';
}

function resolveCapabilities(source: Record<string, unknown>): string[] {
if (Array.isArray(source.capabilities)) {
return source.capabilities.map((item) => String(item)).filter(Boolean);
}
if (Array.isArray(source.skills)) {
return source.skills.map((item) => String(item)).filter(Boolean);
}
return [];
}

function resolveName(member: Record<string, unknown>, type: MemberType): string {
const nameCandidate =
member.name ?? member.fullName ?? member.displayName ?? member.email ?? member.agentName;

if (nameCandidate) return String(nameCandidate);
if (type === 'agent') return String(member.agentId ?? member.id ?? 'AI Agent');
return String(member.userId ?? member.id ?? 'Team Member');
}

function getTeamIdFromContext(): string {
const fromQuery = new URL(window.location.href).searchParams.get('teamId');
if (fromQuery) return fromQuery;
const fromStorage = localStorage.getItem('activeTeamId');
if (fromStorage) return fromStorage;
return 'team-1';
}

async function loadTeamView() {
loading = true;
error = null;

try {
teamId = getTeamIdFromContext();

const [teamResponse, invitesResponse] = await Promise.all([
fetch(`/api/v1/teams/${teamId}`, { credentials: 'include' }),
fetch(`/api/v1/invites?teamId=${teamId}`, { credentials: 'include' })
]);

if (!teamResponse.ok) {
throw new Error('Failed to load team members');
}

const teamPayload = (await teamResponse.json()) as Record<string, unknown>;
const invitePayload = invitesResponse.ok
? ((await invitesResponse.json()) as unknown)
: [];

const teamItems = Array.isArray(teamPayload.members)
? (teamPayload.members as Record<string, unknown>[])
: [];

const inviteItems = Array.isArray(invitePayload)
? (invitePayload as Record<string, unknown>[])
: Array.isArray((invitePayload as Record<string, unknown>).items)
? (((invitePayload as Record<string, unknown>).items as unknown[]) as Record<string, unknown>[])
: [];

const normalizedMembers: TeamMember[] = teamItems.map((member) => {
const type = normalizeType(member.type);
return {
id: String(member.id ?? `${type}-${member.userId ?? member.agentId ?? crypto.randomUUID()}`),
name: resolveName(member, type),
type,
role: String(member.role ?? 'member'),
status: normalizeStatus(member.status),
capabilities: resolveCapabilities(member)
};
});

const normalizedInvites: TeamMember[] = inviteItems.map((invite) => {
const type = normalizeType(invite.type);
return {
id: String(invite.id ?? `${type}-invite-${crypto.randomUUID()}`),
name: String(invite.email ?? invite.name ?? (type === 'agent' ? 'Invited AI Agent' : 'Invited Member')),
type,
role: String(invite.role ?? 'member'),
status: 'invited',
capabilities: resolveCapabilities(invite)
};
});

teamMembers = [...normalizedMembers, ...normalizedInvites];
} catch (loadError) {
error = loadError instanceof Error ? loadError.message : 'Unable to load workforce';
teamMembers = [];
} finally {
loading = false;
}
}

onMount(async () => {
await loadTeamView();
});
</script>

<svelte:head>
<title>Workforce - Convergio</title>
</svelte:head>

<div class="min-h-screen bg-surface-50">
<div class="border-b border-surface-200 bg-white">
<div class="mx-auto flex max-w-7xl items-center justify-between px-4 py-6 sm:px-6 lg:px-8">
<div>
<h1 class="text-2xl font-bold text-surface-900">Workforce</h1>
<p class="mt-1 text-sm text-surface-600">Unified team view for human members and AI agents.</p>
</div>
<div class="flex items-center gap-3">
<button
onclick={loadTeamView}
disabled={loading}
class="inline-flex items-center rounded-lg border border-surface-300 bg-white px-4 py-2 text-sm font-medium text-surface-700 transition-colors hover:bg-surface-50 disabled:opacity-50"
>
Refresh
</button>
<button class="inline-flex items-center rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary-700">
Invite Member
</button>
<button class="inline-flex items-center rounded-lg bg-purple-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-purple-700">
Add Agent
</button>
</div>
</div>
</div>

<div class="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
{#if error}
<div class="mb-6 rounded-lg border border-error-200 bg-error-50 p-4 text-error-700">{error}</div>
{/if}

<div class="overflow-hidden rounded-xl border border-surface-200 bg-white shadow-sm">
<div class="overflow-x-auto">
<table class="min-w-full divide-y divide-surface-200">
<thead class="bg-surface-50">
<tr>
<th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-surface-600">Name</th>
<th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-surface-600">Type</th>
<th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-surface-600">Role</th>
<th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-surface-600">Status</th>
<th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-surface-600">Capabilities</th>
</tr>
</thead>
<tbody class="divide-y divide-surface-100 bg-white">
{#if loading}
<tr>
<td colspan="5" class="px-4 py-8 text-center text-sm text-surface-500">Loading workforce...</td>
</tr>
{:else if teamMembers.length === 0}
<tr>
<td colspan="5" class="px-4 py-8 text-center text-sm text-surface-500">No team members found for this workspace.</td>
</tr>
{:else}
{#each teamMembers as member (member.id)}
<tr>
<td class="px-4 py-3 text-sm font-medium text-surface-900">{member.name}</td>
<td class="px-4 py-3 text-sm text-surface-700">{member.type}</td>
<td class="px-4 py-3 text-sm text-surface-700">{member.role}</td>
<td class="px-4 py-3 text-sm">
<span class={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${statusStyles[member.status]}`}>
{member.status}
</span>
</td>
<td class="px-4 py-3 text-sm text-surface-700">
{#if member.capabilities.length === 0}
<span class="text-surface-400">—</span>
{:else}
{member.capabilities.join(', ')}
{/if}
</td>
</tr>
{/each}
{/if}
</tbody>
</table>
</div>
</div>
</div>
</div>
