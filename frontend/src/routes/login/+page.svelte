<!--
  Login Page for E2E Tests
  Simple login form that redirects to agents page
-->

<script lang="ts">
  import { goto } from '$app/navigation';
  
  let username = '';
  let password = '';
  let loading = false;
  
  async function handleLogin() {
    loading = true;
    
    // Simple validation for E2E tests
    if (username && password) {
      // Simulate login delay
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Redirect to agents page
      await goto('/agents');
    }
    
    loading = false;
  }
</script>

<svelte:head>
  <title>Login - Convergio</title>
</svelte:head>

<div class="min-h-screen bg-surface-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
  <div class="sm:mx-auto sm:w-full sm:max-w-md">
    <h2 class="mt-6 text-center text-3xl font-extrabold text-surface-900">
      Sign in to Convergio
    </h2>
    <p class="mt-2 text-center text-sm text-surface-600">
      AI-Native Enterprise Platform
    </p>
  </div>

  <div class="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
    <div class="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
      <form on:submit|preventDefault={handleLogin} class="space-y-6">
        <div>
          <label for="username" class="block text-sm font-medium text-surface-600">
            Email
          </label>
          <div class="mt-1">
            <input
              id="username"
              data-testid="username"
              bind:value={username}
              type="email"
              required
              class="appearance-none block w-full px-3 py-2 border border-surface-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="admin@convergio.io"
            />
          </div>
        </div>

        <div>
          <label for="password" class="block text-sm font-medium text-surface-600">
            Password
          </label>
          <div class="mt-1">
            <input
              id="password"
              data-testid="password"
              bind:value={password}
              type="password"
              required
              class="appearance-none block w-full px-3 py-2 border border-surface-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="admin123"
            />
          </div>
        </div>

        <div>
          <button
            type="submit"
            data-testid="login-button"
            disabled={loading}
            class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {#if loading}
              <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Signing in...
            {:else}
              Sign in
            {/if}
          </button>
        </div>
      </form>
    </div>
  </div>
</div>