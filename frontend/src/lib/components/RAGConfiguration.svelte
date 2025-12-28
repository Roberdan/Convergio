<script lang="ts">
  import { onMount } from 'svelte';
  import { writable } from 'svelte/store';
  
  export let agentId: string = '';
  export let onSave: (_config: RAGConfig) => void = () => {};
  
  interface RAGConfig {
    enabled: boolean;
    maxTokens: number;
    temperature: number;
    topP: number;
    topK: number;
    chunkSize: number;
    chunkOverlap: number;
    retrievalLimit: number;
    similarityThreshold: number;
    embeddingModel: string;
    vectorStore: string;
    searchType: 'similarity' | 'mmr' | 'hybrid';
    rerankingEnabled: boolean;
    rerankingModel?: string;
    contextWindow: number;
    systemPrompt: string;
    customInstructions: string;
  }
  
  let config: RAGConfig = {
    enabled: true,
    maxTokens: 2048,
    temperature: 0.7,
    topP: 0.9,
    topK: 40,
    chunkSize: 500,
    chunkOverlap: 50,
    retrievalLimit: 5,
    similarityThreshold: 0.75,
    embeddingModel: 'text-embedding-ada-002',
    vectorStore: 'pgvector',
    searchType: 'similarity',
    rerankingEnabled: false,
    rerankingModel: '',
    contextWindow: 4096,
    systemPrompt: '',
    customInstructions: ''
  };
  
  let errors = writable<{[key: string]: string}>({});
  let isDirty = false;
  let isSaving = false;
  let showAdvanced = false;
  
  const embeddingModels = [
    { value: 'text-embedding-ada-002', label: 'OpenAI Ada 002' },
    { value: 'text-embedding-3-small', label: 'OpenAI Small' },
    { value: 'text-embedding-3-large', label: 'OpenAI Large' },
    { value: 'voyage-2', label: 'Voyage 2' },
    { value: 'cohere-embed-v3', label: 'Cohere v3' }
  ];
  
  const vectorStores = [
    { value: 'pgvector', label: 'PostgreSQL pgvector' },
    { value: 'pinecone', label: 'Pinecone' },
    { value: 'weaviate', label: 'Weaviate' },
    { value: 'qdrant', label: 'Qdrant' },
    { value: 'chroma', label: 'ChromaDB' }
  ];
  
  const rerankingModels = [
    { value: 'cohere-rerank-v2', label: 'Cohere Rerank v2' },
    { value: 'bge-reranker-large', label: 'BGE Reranker Large' },
    { value: 'cross-encoder-ms-marco', label: 'MS Marco Cross Encoder' }
  ];
  
  function validateConfig(): boolean {
    const newErrors: {[key: string]: string} = {};
    
    if (config.maxTokens < 1 || config.maxTokens > 32000) {
      newErrors.maxTokens = 'Max tokens must be between 1 and 32000';
    }
    
    if (config.temperature < 0 || config.temperature > 2) {
      newErrors.temperature = 'Temperature must be between 0 and 2';
    }
    
    if (config.topP < 0 || config.topP > 1) {
      newErrors.topP = 'Top P must be between 0 and 1';
    }
    
    if (config.chunkSize < 100 || config.chunkSize > 2000) {
      newErrors.chunkSize = 'Chunk size must be between 100 and 2000';
    }
    
    if (config.chunkOverlap >= config.chunkSize) {
      newErrors.chunkOverlap = 'Chunk overlap must be less than chunk size';
    }
    
    if (config.retrievalLimit < 1 || config.retrievalLimit > 20) {
      newErrors.retrievalLimit = 'Retrieval limit must be between 1 and 20';
    }
    
    if (config.similarityThreshold < 0 || config.similarityThreshold > 1) {
      newErrors.similarityThreshold = 'Similarity threshold must be between 0 and 1';
    }
    
    if (config.contextWindow < 512 || config.contextWindow > 128000) {
      newErrors.contextWindow = 'Context window must be between 512 and 128000';
    }
    
    if (config.rerankingEnabled && !config.rerankingModel) {
      newErrors.rerankingModel = 'Please select a reranking model';
    }
    
    errors.set(newErrors);
    return Object.keys(newErrors).length === 0;
  }
  
  async function loadConfiguration() {
    try {
      const response = await fetch(`/api/agents/${agentId}/rag-config`);
      if (response.ok) {
        const data = await response.json();
        config = { ...config, ...data };
      }
    } catch {
      // Silent failure
    }
  }
  
  async function saveConfiguration() {
    if (!validateConfig()) return;
    
    isSaving = true;
    try {
      const response = await fetch(`/api/agents/${agentId}/rag-config`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
      });
      
      if (response.ok) {
        isDirty = false;
        onSave(config);
      } else {
        throw new Error('Failed to save configuration');
      }
    } catch {
      // Silent failure
      errors.update(e => ({ ...e, save: 'Failed to save configuration' }));
    } finally {
      isSaving = false;
    }
  }
  
  function resetConfiguration() {
    loadConfiguration();
    isDirty = false;
    errors.set({});
  }
  
  function handleInputChange() {
    isDirty = true;
    validateConfig();
  }
  
  onMount(() => {
    if (agentId) {
      loadConfiguration();
    }
  });
</script>

<div class="rag-configuration">
  <div class="config-header">
    <h2>🧠 RAG Configuration</h2>
    <div class="header-actions">
      <label class="toggle-switch">
        <input 
          type="checkbox" 
          bind:checked={config.enabled}
          on:change={handleInputChange}
        />
        <span class="slider"></span>
        <span class="label">{config.enabled ? 'Enabled' : 'Disabled'}</span>
      </label>
    </div>
  </div>
  
  {#if config.enabled}
    <div class="config-sections">
      <!-- Generation Settings -->
      <section class="config-section">
        <h3>Generation Settings</h3>
        
        <div class="form-group">
          <label for="maxTokens">Max Tokens</label>
          <input
            id="maxTokens"
            type="number"
            bind:value={config.maxTokens}
            on:input={handleInputChange}
            min="1"
            max="32000"
            class:error={$errors.maxTokens}
          />
          {#if $errors.maxTokens}
            <span class="error-message">{$errors.maxTokens}</span>
          {/if}
        </div>
        
        <div class="form-row">
          <div class="form-group">
            <label for="temperature">Temperature</label>
            <input
              id="temperature"
              type="number"
              bind:value={config.temperature}
              on:input={handleInputChange}
              min="0"
              max="2"
              step="0.1"
              class:error={$errors.temperature}
            />
            {#if $errors.temperature}
              <span class="error-message">{$errors.temperature}</span>
            {/if}
          </div>
          
          <div class="form-group">
            <label for="topP">Top P</label>
            <input
              id="topP"
              type="number"
              bind:value={config.topP}
              on:input={handleInputChange}
              min="0"
              max="1"
              step="0.1"
              class:error={$errors.topP}
            />
            {#if $errors.topP}
              <span class="error-message">{$errors.topP}</span>
            {/if}
          </div>
          
          <div class="form-group">
            <label for="topK">Top K</label>
            <input
              id="topK"
              type="number"
              bind:value={config.topK}
              on:input={handleInputChange}
              min="1"
              max="100"
            />
          </div>
        </div>
      </section>
      
      <!-- Retrieval Settings -->
      <section class="config-section">
        <h3>Retrieval Settings</h3>
        
        <div class="form-row">
          <div class="form-group">
            <label for="embeddingModel">Embedding Model</label>
            <select
              id="embeddingModel"
              bind:value={config.embeddingModel}
              on:change={handleInputChange}
            >
              {#each embeddingModels as model}
                <option value={model.value}>{model.label}</option>
              {/each}
            </select>
          </div>
          
          <div class="form-group">
            <label for="vectorStore">Vector Store</label>
            <select
              id="vectorStore"
              bind:value={config.vectorStore}
              on:change={handleInputChange}
            >
              {#each vectorStores as store}
                <option value={store.value}>{store.label}</option>
              {/each}
            </select>
          </div>
        </div>
        
        <div class="form-row">
          <div class="form-group">
            <label for="searchType">Search Type</label>
            <select
              id="searchType"
              bind:value={config.searchType}
              on:change={handleInputChange}
            >
              <option value="similarity">Similarity</option>
              <option value="mmr">MMR (Max Marginal Relevance)</option>
              <option value="hybrid">Hybrid</option>
            </select>
          </div>
          
          <div class="form-group">
            <label for="retrievalLimit">Retrieval Limit</label>
            <input
              id="retrievalLimit"
              type="number"
              bind:value={config.retrievalLimit}
              on:input={handleInputChange}
              min="1"
              max="20"
              class:error={$errors.retrievalLimit}
            />
            {#if $errors.retrievalLimit}
              <span class="error-message">{$errors.retrievalLimit}</span>
            {/if}
          </div>
        </div>
        
        <div class="form-group">
          <label for="similarityThreshold">
            Similarity Threshold: <span class="value">{config.similarityThreshold}</span>
          </label>
          <input
            id="similarityThreshold"
            type="range"
            bind:value={config.similarityThreshold}
            on:input={handleInputChange}
            min="0"
            max="1"
            step="0.05"
          />
        </div>
      </section>
      
      <!-- Chunking Settings -->
      <section class="config-section">
        <h3>Document Chunking</h3>
        
        <div class="form-row">
          <div class="form-group">
            <label for="chunkSize">Chunk Size</label>
            <input
              id="chunkSize"
              type="number"
              bind:value={config.chunkSize}
              on:input={handleInputChange}
              min="100"
              max="2000"
              class:error={$errors.chunkSize}
            />
            {#if $errors.chunkSize}
              <span class="error-message">{$errors.chunkSize}</span>
            {/if}
          </div>
          
          <div class="form-group">
            <label for="chunkOverlap">Chunk Overlap</label>
            <input
              id="chunkOverlap"
              type="number"
              bind:value={config.chunkOverlap}
              on:input={handleInputChange}
              min="0"
              max={config.chunkSize - 1}
              class:error={$errors.chunkOverlap}
            />
            {#if $errors.chunkOverlap}
              <span class="error-message">{$errors.chunkOverlap}</span>
            {/if}
          </div>
        </div>
        
        <div class="form-group">
          <label for="contextWindow">Context Window Size</label>
          <input
            id="contextWindow"
            type="number"
            bind:value={config.contextWindow}
            on:input={handleInputChange}
            min="512"
            max="128000"
            class:error={$errors.contextWindow}
          />
          {#if $errors.contextWindow}
            <span class="error-message">{$errors.contextWindow}</span>
          {/if}
        </div>
      </section>
      
      <!-- Advanced Settings -->
      <section class="config-section">
        <button
          class="advanced-toggle"
          on:click={() => showAdvanced = !showAdvanced}
        >
          {showAdvanced ? '▼' : '▶'} Advanced Settings
        </button>
        
        {#if showAdvanced}
          <div class="advanced-settings">
            <div class="form-group">
              <label class="checkbox-label">
                <input
                  type="checkbox"
                  bind:checked={config.rerankingEnabled}
                  on:change={handleInputChange}
                />
                Enable Reranking
              </label>
            </div>
            
            {#if config.rerankingEnabled}
              <div class="form-group">
                <label for="rerankingModel">Reranking Model</label>
                <select
                  id="rerankingModel"
                  bind:value={config.rerankingModel}
                  on:change={handleInputChange}
                  class:error={$errors.rerankingModel}
                >
                  <option value="">Select a model...</option>
                  {#each rerankingModels as model}
                    <option value={model.value}>{model.label}</option>
                  {/each}
                </select>
                {#if $errors.rerankingModel}
                  <span class="error-message">{$errors.rerankingModel}</span>
                {/if}
              </div>
            {/if}
            
            <div class="form-group">
              <label for="systemPrompt">System Prompt</label>
              <textarea
                id="systemPrompt"
                bind:value={config.systemPrompt}
                on:input={handleInputChange}
                rows="4"
                placeholder="Enter system prompt for RAG context..."
              ></textarea>
            </div>
            
            <div class="form-group">
              <label for="customInstructions">Custom Instructions</label>
              <textarea
                id="customInstructions"
                bind:value={config.customInstructions}
                on:input={handleInputChange}
                rows="4"
                placeholder="Additional instructions for retrieval and generation..."
              ></textarea>
            </div>
          </div>
        {/if}
      </section>
    </div>
  {/if}
  
  <div class="config-actions">
    <button
      class="btn btn-secondary"
      on:click={resetConfiguration}
      disabled={!isDirty || isSaving}
    >
      Reset
    </button>
    <button
      class="btn btn-primary"
      on:click={saveConfiguration}
      disabled={!isDirty || isSaving}
    >
      {isSaving ? 'Saving...' : 'Save Configuration'}
    </button>
  </div>
  
  {#if $errors.save}
    <div class="save-error">
      {$errors.save}
    </div>
  {/if}
</div>

<style>
  .rag-configuration {
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem;
    background: white;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
  
  .config-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 2px solid #e5e7eb;
  }
  
  .config-header h2 {
    margin: 0;
    font-size: 1.5rem;
    color: #1f2937;
  }
  
  .toggle-switch {
    position: relative;
    display: inline-flex;
    align-items: center;
    cursor: pointer;
  }
  
  .toggle-switch input {
    opacity: 0;
    width: 0;
    height: 0;
  }
  
  .toggle-switch .slider {
    position: relative;
    display: inline-block;
    width: 50px;
    height: 24px;
    background-color: #cbd5e1;
    border-radius: 24px;
    transition: background-color 0.3s;
  }
  
  .toggle-switch .slider::before {
    content: '';
    position: absolute;
    height: 18px;
    width: 18px;
    left: 3px;
    bottom: 3px;
    background-color: white;
    border-radius: 50%;
    transition: transform 0.3s;
  }
  
  .toggle-switch input:checked + .slider {
    background-color: #4f46e5;
  }
  
  .toggle-switch input:checked + .slider::before {
    transform: translateX(26px);
  }
  
  .toggle-switch .label {
    margin-left: 0.75rem;
    font-weight: 500;
  }
  
  .config-sections {
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }
  
  .config-section {
    padding: 1.5rem;
    background: #f9fafb;
    border-radius: 8px;
  }
  
  .config-section h3 {
    margin: 0 0 1rem 0;
    font-size: 1.1rem;
    color: #374151;
  }
  
  .form-group {
    margin-bottom: 1rem;
  }
  
  .form-group label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: #4b5563;
  }
  
  .form-group .value {
    color: #4f46e5;
    font-weight: 600;
  }
  
  .form-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
  }
  
  input[type="number"],
  input[type="range"],
  select,
  textarea {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 1rem;
    transition: border-color 0.2s;
  }
  
  input[type="range"] {
    padding: 0;
  }
  
  input:focus,
  select:focus,
  textarea:focus {
    outline: none;
    border-color: #4f46e5;
    box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
  }
  
  input.error,
  select.error {
    border-color: #ef4444;
  }
  
  .error-message {
    display: block;
    margin-top: 0.25rem;
    color: #ef4444;
    font-size: 0.875rem;
  }
  
  .checkbox-label {
    display: flex;
    align-items: center;
    cursor: pointer;
  }
  
  .checkbox-label input[type="checkbox"] {
    width: auto;
    margin-right: 0.5rem;
  }
  
  .advanced-toggle {
    background: none;
    border: none;
    color: #4f46e5;
    font-weight: 600;
    cursor: pointer;
    padding: 0.5rem 0;
    font-size: 1rem;
    transition: color 0.2s;
  }
  
  .advanced-toggle:hover {
    color: #4338ca;
  }
  
  .advanced-settings {
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid #e5e7eb;
  }
  
  .config-actions {
    display: flex;
    justify-content: flex-end;
    gap: 1rem;
    margin-top: 2rem;
    padding-top: 2rem;
    border-top: 2px solid #e5e7eb;
  }
  
  .btn {
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 6px;
    font-size: 1rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  .btn-primary {
    background: #4f46e5;
    color: white;
  }
  
  .btn-primary:hover:not(:disabled) {
    background: #4338ca;
  }
  
  .btn-secondary {
    background: #6b7280;
    color: white;
  }
  
  .btn-secondary:hover:not(:disabled) {
    background: #4b5563;
  }
  
  .save-error {
    margin-top: 1rem;
    padding: 1rem;
    background: #fee2e2;
    border: 1px solid #fecaca;
    border-radius: 6px;
    color: #991b1b;
  }
</style>