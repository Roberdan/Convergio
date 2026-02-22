<script lang="ts">
  interface Props {
    agentName: string;
    size?: string;
    className?: string;
  }

  let { agentName, size = "w-6 h-6", className = "" }: Props = $props();

  // Agent-specific color schemes and gradients
  const agentStyles = {
    Ali: { // Chief of Staff - Enso Buddhist symbol (Zen colors for calm/peace)
      colors: ["#1e3a8a", "#3b82f6", "#e0f2fe"],  // Deep blue to light blue - zen, depth, tranquility
      icon: "enso"
    },
    Amy: { // CFO - Financial charts/graphs
      colors: ["#10b981", "#059669"],
      icon: "chart"
    },
    Baccio: { // Tech Architect - Blueprint/structure
      colors: ["#3b82f6", "#2563eb"],
      icon: "blueprint"
    },
    Sofia: { // Marketing Strategist - Megaphone/targeting
      colors: ["#ec4899", "#db2777"],
      icon: "megaphone"
    },
    Luca: { // Security Expert - Shield/lock
      colors: ["#ef4444", "#dc2626"],
      icon: "shield"
    },
    Giulia: { // HR Director - People/team
      colors: ["#8b5cf6", "#7c3aed"],
      icon: "people"
    },
    Marco: { // Operations Director - Gears/process
      colors: ["#4b5563", "#374151"],
      icon: "gears"
    },
    Francesco: { // Legal Advisor - Scale/law
      colors: ["#6366f1", "#4f46e5"],
      icon: "scale"
    },
    Davide: { // Project Manager - Kanban/timeline
      colors: ["#eab308", "#ca8a04"],
      icon: "timeline"
    },
    Omri: { // Data Scientist - Data/analytics
      colors: ["#14b8a6", "#0d9488"],
      icon: "data"
    },
    Elena: { // DevOps Engineer - Cloud/infrastructure
      colors: ["#06b6d4", "#0891b2"],
      icon: "cloud"
    },
    Andrea: { // Sales Director - Target/growth
      colors: ["#22c55e", "#16a34a"],
      icon: "target"
    },
    Chiara: { // UX Designer - Pen/design
      colors: ["#8b5cf6", "#7c3aed"],
      icon: "design"
    },
    Valentina: { // Content Creator - Pen/content
      colors: ["#f43f5e", "#e11d48"],
      icon: "content"
    },
    Matteo: { // Financial Analyst - Calculator/numbers
      colors: ["#64748b", "#475569"],
      icon: "calculator"
    },
    Serena: { // Customer Success - Heart/support
      colors: ["#f59e0b", "#d97706"],
      icon: "heart"
    },
    // Additional agents (17-40)
    Roberto: { // CEO Advisor - Crown/strategy
      colors: ["#7c3aed", "#6d28d9"],
      icon: "crown"
    },
    Alice: { // Innovation Manager - Lightbulb/innovation
      colors: ["#06b6d4", "#0891b2"],
      icon: "lightbulb"
    },
    Tomaso: { // Business Analyst - Analytics/graph
      colors: ["#059669", "#047857"],
      icon: "analytics"
    },
    Diana: { // Quality Assurance - Check/quality
      colors: ["#dc2626", "#b91c1c"],
      icon: "quality"
    },
    Filippo: { // Supply Chain Manager - Truck/supply
      colors: ["#d97706", "#b45309"],
      icon: "truck"
    },
    Camila: { // Brand Manager - Brand/tag
      colors: ["#e11d48", "#be185d"],
      icon: "brand"
    },
    Giovanni: { // Risk Manager - Warning/risk
      colors: ["#dc2626", "#b91c1c"],
      icon: "warning"
    },
    Lucia: { // Training Coordinator - Book/training
      colors: ["#7c3aed", "#6d28d9"],
      icon: "book"
    },
    Alessandro: { // Product Manager - Product/box
      colors: ["#0891b2", "#0e7490"],
      icon: "product"
    },
    Federica: { // Social Media Manager - Share/social
      colors: ["#db2777", "#be185d"],
      icon: "social"
    },
    Riccardo: { // Business Intelligence - Chart/BI
      colors: ["#059669", "#047857"],
      icon: "chart"
    },
    Silvia: { // Compliance Officer - Document/compliance
      colors: ["#4f46e5", "#4338ca"],
      icon: "document"
    },
    Massimo: { // Partnership Manager - Handshake/partnership
      colors: ["#16a34a", "#15803d"],
      icon: "handshake"
    },
    Paola: { // Change Management - Transform/change
      colors: ["#8b5cf6", "#7c3aed"],
      icon: "transform"
    },
    Stefano: { // Network Engineer - Network/wifi
      colors: ["#0891b2", "#0e7490"],
      icon: "network"
    },
    Laura: { // Event Coordinator - Calendar/event
      colors: ["#d97706", "#b45309"],
      icon: "calendar"
    },
    Vincenzo: { // Treasury Manager - Coins/treasury
      colors: ["#059669", "#047857"],
      icon: "coins"
    },
    Elisabetta: { // Corporate Communications - Megaphone/comms
      colors: ["#db2777", "#be185d"],
      icon: "megaphone"
    },
    Antonio: { // Database Administrator - Database/db
      colors: ["#4f46e5", "#4338ca"],
      icon: "database"
    },
    Martina: { // Market Research Analyst - Search/research
      colors: ["#7c3aed", "#6d28d9"],
      icon: "search"
    },
    Daniele: { // System Administrator - Server/system
      colors: ["#475569", "#334155"],
      icon: "server"
    },
    Claudia: { // Sustainability Manager - Leaf/sustainability
      colors: ["#16a34a", "#15803d"],
      icon: "leaf"
    },
    Fabio: { // Procurement Specialist - ShoppingBag/procurement
      colors: ["#d97706", "#b45309"],
      icon: "shopping"
    },
    Francesca: { // Business Development - Growth/business
      colors: ["#16a34a", "#15803d"],
      icon: "growth"
    }
  };

  let style = $derived(agentStyles[agentName as keyof typeof agentStyles] || agentStyles.Ali);
</script>

<div class="relative {size} {className}">
  <svg class="{size} transform-gpu" viewBox="0 0 24 24">
    <defs>
      <linearGradient id="gradient_{agentName}" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" style="stop-color:{style.colors[0]};stop-opacity:1" />
        <stop offset="100%" style="stop-color:{style.colors[1]};stop-opacity:0.8" />
      </linearGradient>
    </defs>

    {#if style.icon === "enso"}
      <!-- Ali - Zen Enso Circle (brush-like texture) -->
      <defs>
        <radialGradient id="ensoZen_{agentName}" cx="30%" cy="30%" r="70%">
          <stop offset="0%" style="stop-color:{style.colors[2]};stop-opacity:0.9" />
          <stop offset="40%" style="stop-color:{style.colors[1]};stop-opacity:0.8" />
          <stop offset="100%" style="stop-color:{style.colors[0]};stop-opacity:0.9" />
        </radialGradient>
      </defs>
      <!-- Main Enso stroke with brush texture -->
      <path 
        d="M 4 12 Q 4 4 12 4 Q 20 4 20 12 Q 20 20 12 20 Q 8 20 6 16"
        fill="none" 
        stroke="url(#ensoZen_{agentName})" 
        stroke-width="3" 
        stroke-linecap="round"
        opacity="0.9"
        style="transform: rotate(-15deg);"
      />
      <!-- Brush texture overlay -->
      <path 
        d="M 4.2 12.1 Q 4.1 4.1 12.1 4.1 Q 19.9 4.1 19.9 12.1 Q 19.8 19.8 12 19.8 Q 8.2 19.9 6.1 16.1"
        fill="none" 
        stroke="url(#ensoZen_{agentName})" 
        stroke-width="2.5" 
        stroke-linecap="round"
        opacity="0.6"
        style="transform: rotate(-15deg);"
        stroke-dasharray="1 0.5"
      />
      <!-- Inner zen void -->
      <circle 
        cx="12" 
        cy="12" 
        r="6" 
        fill="url(#ensoZen_{agentName})" 
        opacity="0.1"
        style="transform: rotate(-15deg);"
      />
    {:else if style.icon === "chart"}
      <!-- Amy - Financial Chart -->
      <path 
        d="M3 12l3-3 3 2 6-6 6 4" 
        stroke="url(#gradient_{agentName})" 
        stroke-width="2" 
        fill="none" 
        stroke-linecap="round" 
        stroke-linejoin="round"
      />
      <rect x="3" y="18" width="2" height="3" fill="url(#gradient_{agentName})" opacity="0.7" />
      <rect x="7" y="16" width="2" height="5" fill="url(#gradient_{agentName})" opacity="0.7" />
      <rect x="11" y="14" width="2" height="7" fill="url(#gradient_{agentName})" opacity="0.7" />
      <rect x="15" y="12" width="2" height="9" fill="url(#gradient_{agentName})" opacity="0.7" />
    {:else if style.icon === "blueprint"}
      <!-- Baccio - Architecture Blueprint -->
      <rect x="3" y="3" width="18" height="18" fill="none" stroke="url(#gradient_{agentName})" stroke-width="2" stroke-dasharray="3 2" />
      <rect x="6" y="6" width="5" height="5" fill="none" stroke="url(#gradient_{agentName})" stroke-width="1.5" />
      <rect x="13" y="6" width="5" height="3" fill="none" stroke="url(#gradient_{agentName})" stroke-width="1.5" />
      <rect x="6" y="13" width="12" height="5" fill="none" stroke="url(#gradient_{agentName})" stroke-width="1.5" />
      <circle cx="8.5" cy="8.5" r="1" fill="url(#gradient_{agentName})" opacity="0.6" />
    {:else if style.icon === "megaphone"}
      <!-- Sofia - Marketing Megaphone -->
      <path 
        d="M8 12l-1.5 1.5L4 12l2.5-1.5L8 12zm0 0l8-3v6l-8-3zm0 0v6" 
        stroke="url(#gradient_{agentName})" 
        stroke-width="2" 
        fill="none" 
        stroke-linecap="round" 
        stroke-linejoin="round"
      />
      <path d="M19 9v6" stroke="url(#gradient_{agentName})" stroke-width="2" stroke-linecap="round" />
      <circle cx="19" cy="9" r="1" fill="url(#gradient_{agentName})" />
      <circle cx="19" cy="15" r="1" fill="url(#gradient_{agentName})" />
    {:else if style.icon === "shield"}
      <!-- Luca - Security Shield -->
      <path 
        d="M12 2L3 7v5c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5z" 
        stroke="url(#gradient_{agentName})" 
        stroke-width="2" 
        fill="url(#gradient_{agentName})" 
        fill-opacity="0.2"
      />
      <path d="M8 12l2 2 4-4" stroke="url(#gradient_{agentName})" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" />
    {:else if style.icon === "people"}
      <!-- Giulia - HR People -->
      <circle cx="9" cy="7" r="3" stroke="url(#gradient_{agentName})" stroke-width="2" fill="none" />
      <path d="M3 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2" stroke="url(#gradient_{agentName})" stroke-width="2" fill="none" stroke-linecap="round" />
      <circle cx="16" cy="7" r="2" stroke="url(#gradient_{agentName})" stroke-width="2" fill="none" />
      <path d="M21 21v-2a3 3 0 0 0-3-3" stroke="url(#gradient_{agentName})" stroke-width="2" fill="none" stroke-linecap="round" />
    {:else if style.icon === "gears"}
      <!-- Marco - Operations Gears -->
      <circle cx="9" cy="12" r="3" stroke="url(#gradient_{agentName})" stroke-width="1.5" fill="none" />
      <circle cx="15" cy="8" r="2" stroke="url(#gradient_{agentName})" stroke-width="1.5" fill="none" />
      <circle cx="15" cy="16" r="2" stroke="url(#gradient_{agentName})" stroke-width="1.5" fill="none" />
      <path d="M9 9l3-1M9 15l3 1M12 12h3" stroke="url(#gradient_{agentName})" stroke-width="1.5" stroke-linecap="round" />
    {:else if style.icon === "scale"}
      <!-- Francesco - Legal Scale -->
      <path d="M12 2v20M8 6l4-4 4 4" stroke="url(#gradient_{agentName})" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
      <path d="M6 10h4l-2 6-2-6zM14 10h4l-2 6-2-6z" stroke="url(#gradient_{agentName})" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" />
      <rect x="4" y="20" width="16" height="2" fill="url(#gradient_{agentName})" />
    {:else if style.icon === "timeline"}
      <!-- Davide - Project Timeline -->
      <rect x="3" y="6" width="18" height="2" fill="url(#gradient_{agentName})" />
      <circle cx="7" cy="7" r="2" fill="url(#gradient_{agentName})" />
      <circle cx="12" cy="7" r="2" fill="url(#gradient_{agentName})" opacity="0.6" />
      <circle cx="17" cy="7" r="2" fill="url(#gradient_{agentName})" opacity="0.3" />
      <rect x="6" y="10" width="2" height="8" fill="url(#gradient_{agentName})" opacity="0.7" />
      <rect x="11" y="12" width="2" height="6" fill="url(#gradient_{agentName})" opacity="0.5" />
      <rect x="16" y="14" width="2" height="4" fill="url(#gradient_{agentName})" opacity="0.3" />
    {:else if style.icon === "data"}
      <!-- Omri - Data Analytics -->
      <circle cx="12" cy="12" r="3" fill="none" stroke="url(#gradient_{agentName})" stroke-width="2" />
      <path d="M12 1v6m0 6v6m11-7h-6m-6 0H1" stroke="url(#gradient_{agentName})" stroke-width="2" />
      <circle cx="12" cy="5" r="2" fill="url(#gradient_{agentName})" opacity="0.7" />
      <circle cx="12" cy="19" r="2" fill="url(#gradient_{agentName})" opacity="0.7" />
      <circle cx="5" cy="12" r="2" fill="url(#gradient_{agentName})" opacity="0.7" />
      <circle cx="19" cy="12" r="2" fill="url(#gradient_{agentName})" opacity="0.7" />
    {:else if style.icon === "cloud"}
      <!-- Elena - Cloud Infrastructure -->
      <path 
        d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z" 
        stroke="url(#gradient_{agentName})" 
        stroke-width="2" 
        fill="url(#gradient_{agentName})" 
        fill-opacity="0.2"
      />
      <circle cx="12" cy="13" r="1.5" fill="url(#gradient_{agentName})" />
      <circle cx="8" cy="15" r="1" fill="url(#gradient_{agentName})" opacity="0.7" />
      <circle cx="16" cy="15" r="1" fill="url(#gradient_{agentName})" opacity="0.7" />
    {:else if style.icon === "target"}
      <!-- Andrea - Sales Target -->
      <circle cx="12" cy="12" r="8" stroke="url(#gradient_{agentName})" stroke-width="2" fill="none" />
      <circle cx="12" cy="12" r="5" stroke="url(#gradient_{agentName})" stroke-width="2" fill="none" />
      <circle cx="12" cy="12" r="2" fill="url(#gradient_{agentName})" />
      <path d="M12 2v4M12 18v4M2 12h4M18 12h4" stroke="url(#gradient_{agentName})" stroke-width="2" stroke-linecap="round" />
    {:else if style.icon === "design"}
      <!-- Chiara - UX Design -->
      <path d="M12 19l7-7 3 3-7 7-3-3z" stroke="url(#gradient_{agentName})" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" />
      <path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z" stroke="url(#gradient_{agentName})" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" />
      <path d="M2 2l7.586 7.586" stroke="url(#gradient_{agentName})" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
      <circle cx="11" cy="11" r="2" stroke="url(#gradient_{agentName})" stroke-width="2" fill="none" />
    {:else if style.icon === "content"}
      <!-- Valentina - Content Creation -->
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="url(#gradient_{agentName})" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" />
      <path d="M14 2v6h6" stroke="url(#gradient_{agentName})" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" />
      <path d="M16 13H8M16 17H8M10 9H8" stroke="url(#gradient_{agentName})" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
    {:else if style.icon === "calculator"}
      <!-- Matteo - Financial Calculator -->
      <rect x="4" y="2" width="16" height="20" rx="2" stroke="url(#gradient_{agentName})" stroke-width="2" fill="none" />
      <rect x="6" y="6" width="12" height="3" fill="url(#gradient_{agentName})" opacity="0.3" />
      <circle cx="8" cy="12" r="1" fill="url(#gradient_{agentName})" />
      <circle cx="12" cy="12" r="1" fill="url(#gradient_{agentName})" />
      <circle cx="16" cy="12" r="1" fill="url(#gradient_{agentName})" />
      <circle cx="8" cy="16" r="1" fill="url(#gradient_{agentName})" />
      <circle cx="12" cy="16" r="1" fill="url(#gradient_{agentName})" />
      <circle cx="16" cy="16" r="1" fill="url(#gradient_{agentName})" />
    {:else if style.icon === "heart"}
      <!-- Serena - Customer Success Heart -->
      <path 
        d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" 
        stroke="url(#gradient_{agentName})" 
        stroke-width="2" 
        fill="url(#gradient_{agentName})" 
        fill-opacity="0.2"
      />
      <circle cx="12" cy="10" r="1" fill="url(#gradient_{agentName})" />
    {:else if style.icon === "crown"}
      <!-- Roberto - CEO Advisor Crown -->
      <path d="M5 20h14l2-8-3 2-2-4-4 3-4-3-2 4-3-2 2 8z" stroke="url(#gradient_{agentName})" stroke-width="2" fill="url(#gradient_{agentName})" fill-opacity="0.2" stroke-linejoin="round" />
      <circle cx="7" cy="8" r="1" fill="url(#gradient_{agentName})" />
      <circle cx="12" cy="5" r="1" fill="url(#gradient_{agentName})" />
      <circle cx="17" cy="8" r="1" fill="url(#gradient_{agentName})" />
    {:else if style.icon === "lightbulb"}
      <!-- Alice - Innovation Lightbulb -->
      <path d="M9 21h6M12 3a6 6 0 0 0-6 6c0 2 1 3 2 4v2a2 2 0 0 0 2 2h4a2 2 0 0 0 2-2v-2c1-1 2-2 2-4a6 6 0 0 0-6-6z" stroke="url(#gradient_{agentName})" stroke-width="2" fill="url(#gradient_{agentName})" fill-opacity="0.2" stroke-linecap="round" stroke-linejoin="round" />
      <circle cx="12" cy="9" r="1" fill="url(#gradient_{agentName})" />
    {:else if style.icon === "analytics"}
      <!-- Tomaso - Analytics Chart -->
      <rect x="3" y="3" width="18" height="18" rx="2" stroke="url(#gradient_{agentName})" stroke-width="2" fill="none" />
      <path d="M7 14l3-3 2 2 5-5" stroke="url(#gradient_{agentName})" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" />
      <circle cx="7" cy="14" r="1" fill="url(#gradient_{agentName})" />
      <circle cx="10" cy="11" r="1" fill="url(#gradient_{agentName})" />
      <circle cx="12" cy="13" r="1" fill="url(#gradient_{agentName})" />
      <circle cx="17" cy="8" r="1" fill="url(#gradient_{agentName})" />
    {:else if style.icon === "quality"}
      <!-- Diana - Quality Check -->
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="url(#gradient_{agentName})" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" />
      <path d="M22 4L12 14l-3-3" stroke="url(#gradient_{agentName})" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" />
    {:else if style.icon === "truck"}
      <!-- Filippo - Supply Chain Truck -->
      <rect x="1" y="3" width="15" height="13" rx="2" stroke="url(#gradient_{agentName})" stroke-width="2" fill="url(#gradient_{agentName})" fill-opacity="0.2" />
      <path d="M16 8h2l3 3v5H5" stroke="url(#gradient_{agentName})" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" />
      <circle cx="5.5" cy="18.5" r="2.5" stroke="url(#gradient_{agentName})" stroke-width="2" fill="none" />
      <circle cx="18.5" cy="18.5" r="2.5" stroke="url(#gradient_{agentName})" stroke-width="2" fill="none" />
    {:else if style.icon === "brand"}
      <!-- Camila - Brand Tag -->
      <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z" stroke="url(#gradient_{agentName})" stroke-width="2" fill="url(#gradient_{agentName})" fill-opacity="0.2" />
      <circle cx="7" cy="7" r="1.5" fill="url(#gradient_{agentName})" />
    {:else if style.icon === "warning"}
      <!-- Giovanni - Risk Warning -->
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" stroke="url(#gradient_{agentName})" stroke-width="2" fill="url(#gradient_{agentName})" fill-opacity="0.2" />
      <path d="M12 9v4M12 17h.01" stroke="url(#gradient_{agentName})" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
    {:else if style.icon === "book"}
      <!-- Lucia - Training Book -->
      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" stroke="url(#gradient_{agentName})" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" />
      <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" stroke="url(#gradient_{agentName})" stroke-width="2" fill="url(#gradient_{agentName})" fill-opacity="0.2" />
      <path d="M8 7h8M8 11h6" stroke="url(#gradient_{agentName})" stroke-width="1.5" stroke-linecap="round" />
    {:else if style.icon === "product"}
      <!-- Alessandro - Product Box -->
      <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" stroke="url(#gradient_{agentName})" stroke-width="2" fill="url(#gradient_{agentName})" fill-opacity="0.2" />
      <path d="M3.27 6.96L12 12.01l8.73-5.05M12 22.08V12" stroke="url(#gradient_{agentName})" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
    {:else if style.icon === "social"}
      <!-- Federica - Social Share -->
      <circle cx="18" cy="5" r="3" stroke="url(#gradient_{agentName})" stroke-width="2" fill="none" />
      <circle cx="6" cy="12" r="3" stroke="url(#gradient_{agentName})" stroke-width="2" fill="none" />
      <circle cx="18" cy="19" r="3" stroke="url(#gradient_{agentName})" stroke-width="2" fill="none" />
      <path d="M8.59 13.51L15.42 17.49M15.41 6.51L8.59 10.49" stroke="url(#gradient_{agentName})" stroke-width="2" />
    {:else if style.icon === "document"}
      <!-- Silvia - Compliance Document -->
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="url(#gradient_{agentName})" stroke-width="2" fill="url(#gradient_{agentName})" fill-opacity="0.2" />
      <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8" stroke="url(#gradient_{agentName})" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
      <circle cx="11" cy="13" r="1" fill="url(#gradient_{agentName})" />
    {:else if style.icon === "handshake"}
      <!-- Massimo - Partnership Handshake -->
      <path d="M11 12h2a2 2 0 1 1 0 4h-3c-.6 0-1.1.2-1.4.6L3 22" stroke="url(#gradient_{agentName})" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" />
      <path d="M8 11V7a4 4 0 0 1 8 0v4" stroke="url(#gradient_{agentName})" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" />
      <path d="M16 12h1a2 2 0 0 1 0 4h-3" stroke="url(#gradient_{agentName})" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" />
    {:else if style.icon === "transform"}
      <!-- Paola - Change Transform -->
      <path d="M14.828 14.828a4 4 0 0 1-5.656 0M9 10h1a4 4 0 0 1 4 4v1M15 14h1a4 4 0 0 1 4 4v1" stroke="url(#gradient_{agentName})" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" />
      <path d="M21 12c0 4.97-4.03 9-9 9s-9-4.03-9-9 4.03-9 9-9 9 4.03 9 9z" stroke="url(#gradient_{agentName})" stroke-width="2" fill="none" />
      <path d="M16 8l4-4-4-4M8 16l-4 4 4 4" stroke="url(#gradient_{agentName})" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" />
    {:else if style.icon === "network"}
      <!-- Stefano - Network -->
      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" stroke="url(#gradient_{agentName})" stroke-width="2" fill="none" />
      <circle cx="12" cy="8" r="2" fill="url(#gradient_{agentName})" />
    {:else if style.icon === "calendar"}
      <!-- Laura - Calendar -->
      <rect x="3" y="4" width="18" height="18" rx="2" stroke="url(#gradient_{agentName})" stroke-width="2" fill="url(#gradient_{agentName})" fill-opacity="0.1" />
      <path d="M16 2v4M8 2v4M3 10h18" stroke="url(#gradient_{agentName})" stroke-width="2" stroke-linecap="round" />
      <circle cx="8" cy="14" r="1" fill="url(#gradient_{agentName})" />
      <circle cx="12" cy="14" r="1" fill="url(#gradient_{agentName})" />
      <circle cx="16" cy="14" r="1" fill="url(#gradient_{agentName})" />
    {:else if style.icon === "coins"}
      <!-- Vincenzo - Treasury Coins -->
      <circle cx="8" cy="8" r="6" stroke="url(#gradient_{agentName})" stroke-width="2" fill="url(#gradient_{agentName})" fill-opacity="0.2" />
      <path d="M16 8a6 6 0 0 0-6-6c-3 0-6 3-6 6s3 6 6 6c3 0 6-3 6-6z" stroke="url(#gradient_{agentName})" stroke-width="2" fill="none" />
      <circle cx="16" cy="16" r="6" stroke="url(#gradient_{agentName})" stroke-width="2" fill="none" />
      <path d="M8 8h.01M16 16h.01" stroke="url(#gradient_{agentName})" stroke-width="2" stroke-linecap="round" />
    {:else if style.icon === "database"}
      <!-- Antonio - Database -->
      <ellipse cx="12" cy="5" rx="9" ry="3" stroke="url(#gradient_{agentName})" stroke-width="2" fill="url(#gradient_{agentName})" fill-opacity="0.2" />
      <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" stroke="url(#gradient_{agentName})" stroke-width="2" fill="none" />
      <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" stroke="url(#gradient_{agentName})" stroke-width="2" fill="none" />
    {:else if style.icon === "search"}
      <!-- Martina - Search -->
      <circle cx="11" cy="11" r="8" stroke="url(#gradient_{agentName})" stroke-width="2" fill="none" />
      <path d="M21 21l-4.35-4.35" stroke="url(#gradient_{agentName})" stroke-width="2" stroke-linecap="round" />
      <circle cx="11" cy="11" r="3" fill="url(#gradient_{agentName})" fill-opacity="0.3" />
    {:else if style.icon === "server"}
      <!-- Daniele - Server -->
      <rect x="2" y="3" width="20" height="4" rx="1" stroke="url(#gradient_{agentName})" stroke-width="2" fill="url(#gradient_{agentName})" fill-opacity="0.2" />
      <rect x="2" y="10" width="20" height="4" rx="1" stroke="url(#gradient_{agentName})" stroke-width="2" fill="url(#gradient_{agentName})" fill-opacity="0.2" />
      <rect x="2" y="17" width="20" height="4" rx="1" stroke="url(#gradient_{agentName})" stroke-width="2" fill="url(#gradient_{agentName})" fill-opacity="0.2" />
      <circle cx="6" cy="5" r="1" fill="url(#gradient_{agentName})" />
      <circle cx="6" cy="12" r="1" fill="url(#gradient_{agentName})" />
      <circle cx="6" cy="19" r="1" fill="url(#gradient_{agentName})" />
    {:else if style.icon === "leaf"}
      <!-- Claudia - Sustainability Leaf -->
      <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10z" stroke="url(#gradient_{agentName})" stroke-width="2" fill="url(#gradient_{agentName})" fill-opacity="0.3" />
      <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12" stroke="url(#gradient_{agentName})" stroke-width="2" fill="none" stroke-linecap="round" />
    {:else if style.icon === "shopping"}
      <!-- Fabio - Shopping Bag -->
      <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z" stroke="url(#gradient_{agentName})" stroke-width="2" fill="url(#gradient_{agentName})" fill-opacity="0.2" />
      <path d="M3 6h18M8 10a4 4 0 0 0 8 0" stroke="url(#gradient_{agentName})" stroke-width="2" stroke-linecap="round" />
    {:else if style.icon === "growth"}
      <!-- Francesca - Growth Arrow -->
      <path d="M3 3v18h18" stroke="url(#gradient_{agentName})" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
      <path d="M13 17l8-8-8 3V9z" stroke="url(#gradient_{agentName})" stroke-width="2" fill="url(#gradient_{agentName})" fill-opacity="0.3" stroke-linejoin="round" />
      <path d="M7 13l4-4 4 2 6-6" stroke="url(#gradient_{agentName})" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" />
    {/if}
  </svg>
</div>