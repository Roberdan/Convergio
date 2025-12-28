<script lang="ts">
  import { marked } from 'marked';
  import hljs from 'highlight.js';
  import 'highlight.js/styles/github-dark.css';

  export let content: string = '';

  let renderedHtml = '';

  // Configure marked with syntax highlighting using hooks
  marked.use({
    async: false,
    breaks: true,
    gfm: true,
    hooks: {
      postprocess(html: string) {
        return html;
      }
    }
  });

  // Set up custom renderer for code blocks
  const renderer = new marked.Renderer();

  renderer.code = function({ text, lang }: { text: string; lang?: string }): string {
    if (lang && hljs.getLanguage(lang)) {
      try {
        const highlighted = hljs.highlight(text, { language: lang }).value;
        return `<pre><code class="hljs language-${lang}">${highlighted}</code></pre>`;
      } catch {
        // Silent failure
      }
    }
    return `<pre><code>${text}</code></pre>`;
  };

  marked.use({ renderer });

  $: if (content) {
    const parsed = marked.parse(content);
    renderedHtml = typeof parsed === 'string' ? parsed : '';
  }
</script>

<div class="markdown-content prose prose-sm max-w-none">
  {@html renderedHtml}
</div>

<style>
  :global(.markdown-content) {
    color: inherit;
    line-height: 1.6;
  }

  :global(.markdown-content h1) {
    font-size: 1.5rem;
    font-weight: 700;
    margin-top: 1rem;
    margin-bottom: 0.5rem;
  }

  :global(.markdown-content h2) {
    font-size: 1.25rem;
    font-weight: 600;
    margin-top: 1rem;
    margin-bottom: 0.5rem;
  }

  :global(.markdown-content h3) {
    font-size: 1.1rem;
    font-weight: 600;
    margin-top: 0.75rem;
    margin-bottom: 0.5rem;
  }

  :global(.markdown-content p) {
    margin-bottom: 0.75rem;
  }

  :global(.markdown-content ul, .markdown-content ol) {
    margin-left: 1.5rem;
    margin-bottom: 0.75rem;
  }

  :global(.markdown-content li) {
    margin-bottom: 0.25rem;
  }

  :global(.markdown-content code) {
    background-color: rgba(0, 0, 0, 0.05);
    padding: 0.125rem 0.25rem;
    border-radius: 0.25rem;
    font-size: 0.875rem;
    font-family: 'JetBrains Mono', monospace;
  }

  :global(.markdown-content pre) {
    background-color: #1a1b26;
    padding: 1rem;
    border-radius: 0.5rem;
    overflow-x: auto;
    margin-bottom: 1rem;
  }

  :global(.markdown-content pre code) {
    background-color: transparent;
    padding: 0;
    color: #e4e4e7;
  }

  :global(.markdown-content blockquote) {
    border-left: 4px solid #3b82f6;
    padding-left: 1rem;
    margin: 1rem 0;
    color: #6b7280;
    font-style: italic;
  }

  :global(.markdown-content strong) {
    font-weight: 600;
  }

  :global(.markdown-content em) {
    font-style: italic;
  }

  :global(.markdown-content a) {
    color: #3b82f6;
    text-decoration: underline;
  }

  :global(.markdown-content a:hover) {
    color: #2563eb;
  }

  :global(.markdown-content table) {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 1rem;
  }

  :global(.markdown-content th) {
    background-color: #f3f4f6;
    padding: 0.5rem;
    text-align: left;
    font-weight: 600;
    border: 1px solid #e5e7eb;
  }

  :global(.markdown-content td) {
    padding: 0.5rem;
    border: 1px solid #e5e7eb;
  }

  :global(.markdown-content hr) {
    margin: 1.5rem 0;
    border: none;
    border-top: 1px solid #e5e7eb;
  }

  /* Dark mode adjustments */
  :global(.dark .markdown-content code) {
    background-color: rgba(255, 255, 255, 0.1);
  }

  :global(.dark .markdown-content blockquote) {
    color: #9ca3af;
  }

  :global(.dark .markdown-content th) {
    background-color: #374151;
  }

  :global(.dark .markdown-content td), 
  :global(.dark .markdown-content th) {
    border-color: #4b5563;
  }

  :global(.dark .markdown-content hr) {
    border-color: #4b5563;
  }
</style>