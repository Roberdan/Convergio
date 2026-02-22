<script lang="ts">
  import { goto } from '$app/navigation';

  type WaitlistState = 'idle' | 'submitting' | 'success' | 'error';

  const features = [
    {
      title: 'Multi-agent orchestration',
      description: 'Coordinate specialized AI agents in one mission-ready workspace.'
    },
    {
      title: 'Cost tracking',
      description: 'Track model spend in real-time with transparent usage visibility.'
    },
    {
      title: 'Team management',
      description: 'Invite and align people, agents, and workflows around outcomes.'
    },
    {
      title: 'AI providers',
      description: 'Run across OpenAI, Anthropic, and more from one control plane.'
    }
  ];

  const showcasedAgents = [
    {
      name: 'Ali • Chief of Staff',
      focus: 'Cross-functional execution and strategic briefings.'
    },
    {
      name: 'Maya • Growth Strategist',
      focus: 'Pipeline design, campaigns, and conversion experiments.'
    },
    {
      name: 'Noah • Finance Analyst',
      focus: 'Cost control, forecast scenarios, and budget optimization.'
    }
  ];

  let activeAgentIndex = $state(0);
  let email = $state('');
  let company = $state('');
  let waitlistState = $state<WaitlistState>('idle');
  let waitlistMessage = $state('');

  function nextAgent() {
    activeAgentIndex = (activeAgentIndex + 1) % showcasedAgents.length;
  }

  function previousAgent() {
    activeAgentIndex = (activeAgentIndex - 1 + showcasedAgents.length) % showcasedAgents.length;
  }

  async function submitWaitlist(event: SubmitEvent) {
    event.preventDefault();
    if (!email.trim()) return;

    waitlistState = 'submitting';
    waitlistMessage = '';

    try {
      const response = await fetch('/api/v1/waitlist', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email: email.trim(), company: company.trim() || undefined })
      });

      if (!response.ok) {
        throw new Error('Unable to join waitlist');
      }

      waitlistState = 'success';
      waitlistMessage = 'You are on the waitlist. We will contact you soon.';
      email = '';
      company = '';
    } catch {
      waitlistState = 'error';
      waitlistMessage = 'Something went wrong. Please try again in a moment.';
    }
  }
</script>

<div class="min-h-screen bg-surface-50 text-surface-900">
  <section class="hero max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 pb-14">
    <div class="text-center">
      <p class="text-sm uppercase tracking-[0.2em] text-blue-600 font-semibold">Convergio</p>
      <h1 class="mt-4 text-4xl md:text-5xl font-bold leading-tight">Human purpose. AI momentum.</h1>
      <p class="mt-5 text-lg text-surface-600 max-w-3xl mx-auto">
        Build outcomes with autonomous teams of agents while keeping humans in command.
      </p>
      <div class="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
        <button
          class="px-6 py-3 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 transition-colors"
          onclick={() => goto('/login')}
        >
          Start free trial
        </button>
        <button
          class="px-6 py-3 rounded-lg border border-surface-300 bg-white hover:bg-surface-100 transition-colors"
          onclick={() => goto('/dashboard')}
        >
          View product tour
        </button>
      </div>
    </div>
  </section>

  <section class="features max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      {#each features as feature}
        <article class="rounded-xl border border-surface-200 bg-white p-6">
          <h2 class="text-lg font-semibold text-surface-900">{feature.title}</h2>
          <p class="mt-2 text-surface-600">{feature.description}</p>
        </article>
      {/each}
    </div>
  </section>

  <section class="pricing max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <h2 class="text-2xl font-bold text-center mb-8">Pricing</h2>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <article class="rounded-xl border border-surface-300 bg-white p-6">
        <p class="text-sm font-semibold text-blue-600">Trial</p>
        <p class="mt-2 text-3xl font-bold">Free</p>
        <ul class="mt-4 space-y-2 text-surface-700">
          <li>• Core orchestration workspace</li>
          <li>• Shared AI provider access</li>
          <li>• 14-day onboarding support</li>
        </ul>
      </article>
      <article class="rounded-xl border-2 border-blue-600 bg-white p-6 shadow-sm">
        <p class="text-sm font-semibold text-blue-700">Pro</p>
        <p class="mt-2 text-3xl font-bold">Custom</p>
        <ul class="mt-4 space-y-2 text-surface-700">
          <li>• Unlimited multi-agent missions</li>
          <li>• Advanced cost governance</li>
          <li>• Team roles and approval flows</li>
        </ul>
      </article>
    </div>
  </section>

  <section class="waitlist max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <div class="rounded-2xl border border-surface-300 bg-white p-8">
      <h2 class="text-2xl font-bold">Join the waitlist</h2>
      <p class="mt-2 text-surface-600">Get early access to enterprise-grade AI coordination.</p>
      <form class="mt-6 grid grid-cols-1 md:grid-cols-3 gap-3" onsubmit={submitWaitlist}>
        <input
          class="rounded-lg border border-surface-300 px-3 py-2 md:col-span-1"
          type="email"
          bind:value={email}
          required
          placeholder="you@company.com"
        />
        <input
          class="rounded-lg border border-surface-300 px-3 py-2 md:col-span-1"
          type="text"
          bind:value={company}
          placeholder="Company (optional)"
        />
        <button
          class="rounded-lg bg-blue-600 text-white font-semibold px-4 py-2 hover:bg-blue-700 disabled:opacity-70"
          disabled={waitlistState === 'submitting'}
          type="submit"
        >
          {waitlistState === 'submitting' ? 'Submitting...' : 'Join waitlist'}
        </button>
      </form>
      {#if waitlistMessage}
        <p class="mt-3 text-sm {waitlistState === 'error' ? 'text-red-600' : 'text-emerald-700'}">{waitlistMessage}</p>
      {/if}
    </div>
  </section>

  <section class="carousel max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 pb-16">
    <h2 class="text-2xl font-bold text-center">Agent showcase carousel</h2>
    <article class="mt-6 rounded-xl border border-surface-300 bg-white p-6 text-center">
      <p class="text-sm text-blue-600 font-semibold">{showcasedAgents[activeAgentIndex].name}</p>
      <p class="mt-2 text-surface-700">{showcasedAgents[activeAgentIndex].focus}</p>
      <div class="mt-5 flex justify-center gap-2">
        <button class="px-3 py-1 rounded border border-surface-300" onclick={previousAgent}>Previous</button>
        <button class="px-3 py-1 rounded border border-surface-300" onclick={nextAgent}>Next</button>
      </div>
    </article>
  </section>
</div>
