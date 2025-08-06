# 🎨 Convergio2030 Frontend

Modern SvelteKit frontend per la piattaforma Convergio2030 unificata.

## 🚀 Quick Start

```bash
# Installa dipendenze
npm install

# Avvia dev server (porta 4000)
npm run dev

# Build per produzione
npm run build
```

## 🏗️ Architettura

```
src/
├── routes/                 # SvelteKit routes
│   ├── +layout.svelte     # Layout globale
│   ├── +page.svelte       # Home page
│   ├── login/             # Pagina login
│   └── (app)/             # App protetta
│       ├── +layout.svelte # Layout app autenticata
│       ├── dashboard/     # Dashboard principale
│       ├── agents/        # Chat AI agents
│       ├── vector/        # Vector search
│       └── analytics/     # Analytics & costs
├── lib/
│   ├── auth/              # Sistema autenticazione
│   │   ├── auth.store.ts  # Svelte store per auth state
│   │   ├── auth.types.ts  # Type definitions
│   │   └── auth.utils.ts  # Utilities auth
│   ├── components/        # Componenti riutilizzabili
│   │   └── Navigation.svelte # Menu navigazione
│   └── api-client.ts      # Client API unificato
├── app.css               # Tailwind + design system
└── app.html              # Template HTML base
```

## 🔐 Autenticazione

Sistema di autenticazione **completamente sicuro** integrato con il backend:

### Features
- **JWT RS256** con refresh automatico
- **Svelte stores** per gestione stato
- **Route protection** automatica
- **Token persistence** in localStorage
- **Auto-redirect** su scadenza token

### Utilizzo
```typescript
import { authStore, isAuthenticated, currentUser } from '$lib/auth/auth.store';

// Login
await authStore.login(username, password);

// Logout  
await authStore.logout();

// Check auth status
$isAuthenticated // true/false
$currentUser     // User object
```

## 🤖 AI Agents Integration

Chat interface per tutti i **50+ agenti reali**:

### Features
- **Lista agenti dinamica** dal backend
- **Chat interface moderna** con cronologia
- **Execution tracking** in tempo reale
- **Error handling** robusto
- **Responsive design** mobile-friendly

### Componenti
- `routes/(app)/agents/+page.svelte` - Pagina principale agenti
- Lista agenti dinamica con metadata
- Chat interface con typing indicators
- History management con localStorage

## 🎨 Design System

Design system basato su **Tailwind CSS** con tema custom:

### Colori
```css
/* Convergio Brand Colors */
primary: blue (0ea5e9 → 0c4a6e)
gray: slate (f8fafc → 020617)  
surface: dark mode colors

/* Semantic Colors */
success: green
warning: yellow  
error: red
```

### Componenti CSS
```css
/* Buttons */
.btn, .btn-primary, .btn-secondary, .btn-outline, .btn-ghost

/* Forms */  
.input, .card, .badge

/* Layout */
.card, .card-header, .card-content, .card-footer
```

### Dark Mode
Supporto completo dark mode con:
- Classi CSS custom properties
- Toggle automatico tema sistema
- Persistenza preferenze utente

## 📱 Responsive Design

Design **mobile-first** con breakpoints:

```css
sm: 640px   # Smartphone landscape
md: 768px   # Tablet  
lg: 1024px  # Desktop
xl: 1280px  # Large desktop
```

### Navigation
- **Desktop**: Menu orizzontale con dropdown utente
- **Mobile**: Hamburger menu con overlay
- **Tablet**: Layout adattivo automatico

## 🔗 API Integration

Client API unificato per comunicazione backend:

### Features
- **Automatic auth headers** con JWT
- **Error handling** centralizzato  
- **Request/response interceptors**
- **Timeout management**
- **Retry logic** su fallimenti rete

### Utilizzo
```typescript
import { api } from '$lib/api-client';

// Agenti
const agents = await api.getAgents();
const result = await api.executeAgent('ali-chief-of-staff', 'Hello');

// Vector search
const docs = await api.searchDocuments('query di ricerca');

// Analytics  
const dashboard = await api.getDashboard('7d');
const metrics = await api.getMetrics();
```

## 🧪 Testing

Setup completo per testing:

### Unit Tests
```bash
npm run test       # Vitest
npm run test:ui    # Vitest UI
npm run coverage   # Coverage report
```

### E2E Tests  
```bash
npm run test:e2e        # Playwright
npm run test:e2e:ui     # Playwright UI
npm run test:e2e:debug  # Debug mode
```

### Storybook
```bash
npm run storybook       # Component stories
npm run build-storybook # Build stories
```

## 🔧 Development

### Scripts Disponibili
```bash
npm run dev           # Dev server (porta 4000)
npm run build         # Build produzione
npm run preview       # Preview build
npm run check         # Type checking
npm run lint          # ESLint + Prettier
npm run format        # Auto-format codice
```

### Environment Variables
```bash
# .env.local
CONVERGIO2030_API_URL=http://localhost:9000
CONVERGIO2030_ENV=development
```

### Proxy Configuration
Il dev server è configurato per proxy automatico delle API:

```typescript
// vite.config.ts
server: {
  proxy: {
    '/api': 'http://localhost:9000',
    '/health': 'http://localhost:9000'
  }
}
```

## 🚀 Build & Deploy

### Development
```bash
npm run dev
# Apri http://localhost:4000
```

### Production Build
```bash
npm run build
npm run preview
```

### Docker (Opzionale)
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 4000
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0"]
```

## 📊 Performance

### Bundle Size
- **Main bundle**: ~150KB gzipped
- **Vendor chunks**: Separati automaticamente
- **Code splitting**: Route-based automatico
- **Tree shaking**: Ottimizzazione automatica

### Lighthouse Score
Target produzione:
- **Performance**: 90+
- **Accessibility**: 95+  
- **Best Practices**: 90+
- **SEO**: 90+

## 🔒 Security

### Headers Sicurezza
```typescript
// hooks.server.ts
response.headers.set('X-Frame-Options', 'DENY');
response.headers.set('X-Content-Type-Options', 'nosniff');
response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
```

### Content Security Policy
```html
<!-- CSP automatica in produzione -->
script-src 'self'; 
style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
connect-src 'self' http://localhost:9000;
```

### Auth Security
- **JWT validation** su ogni request
- **Auto-logout** su token scaduto
- **Secure storage** con TTL
- **CSRF protection** built-in SvelteKit

## 🎯 Features Principali

### ✅ Implementate
- 🔐 **Autenticazione JWT completa**
- 🏠 **Dashboard con metriche real-time**  
- 🤖 **Chat con 50+ AI agents reali**
- 🔍 **Vector search interface**
- 📊 **Analytics e cost management**
- 📱 **Design responsive**
- 🌙 **Dark mode support**
- 🔒 **Security headers**

### 🚧 Roadmap
- 📋 **Profile management**
- ⚙️ **Settings panel**  
- 📄 **Document upload UI**
- 📈 **Advanced charts**
- 🔔 **Real-time notifications**
- 👥 **Multi-user features**

---

**Frontend moderno, sicuro e performante per Convergio2030** 🚀