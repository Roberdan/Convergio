<script lang="ts">
  import { page } from '$app/stores';

  interface Props {
    children?: import('svelte').Snippet;
  }

  let { children }: Props = $props();

  const navItems = [
    { href: '/admin/users', label: 'Users' },
    { href: '/admin/audit', label: 'Audit Log' },
    { href: '/admin/tiers', label: 'Tiers' },
    { href: '/admin/agents', label: 'Agents' },
    { href: '/admin/waitlist', label: 'Waitlist' }
  ];

  function isActive(href: string): boolean {
    return $page.url.pathname === href;
  }
</script>

<div class="min-h-screen bg-slate-50">
  <div class="mx-auto grid max-w-7xl gap-6 px-4 py-6 lg:grid-cols-[240px_1fr]">
    <aside class="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h1 class="mb-4 text-lg font-semibold text-slate-900">Admin Console</h1>
      <nav class="space-y-1" aria-label="Admin">
        {#each navItems as item}
          <a
            href={item.href}
            class="block rounded-md px-3 py-2 text-sm font-medium transition {isActive(item.href)
              ? 'bg-blue-600 text-white'
              : 'text-slate-700 hover:bg-slate-100'}"
          >
            {item.label}
          </a>
        {/each}
      </nav>
    </aside>

    <main class="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      {@render children?.()}
    </main>
  </div>
</div>
