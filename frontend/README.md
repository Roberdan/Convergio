# 🎨 Convergio Frontend

Modern SvelteKit frontend for the unified Convergio platform.

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Start dev server (port 4000)
npm run dev

# Build for production
npm run build
```

## 🏗️ Architecture

```
src/
├── routes/                 # SvelteKit routes
│   ├── +layout.svelte     # Global layout
│   ├── +page.svelte       # Home page
│   ├── login/             # Login page
│   └── (app)/             # Protected app
│       ├── +layout.svelte # Authenticated app layout
│       ├── dashboard/     # Main dashboard
│       ├── agents/        # AI agents chat
│       ├── vector/        # Vector search
│       └── analytics/     # Analytics & costs
├── lib/
│   ├── auth/              # Authentication system
│   │   ├── auth.store.ts  # Svelte store for auth state
│   │   ├── auth.types.ts  # Type definitions
│   │   └── auth.utils.ts  # Auth utilities
│   ├── components/        # Reusable components
│   │   └── Navigation.svelte # Navigation menu
│   └── api-client.ts      # Unified API client
├── app.css               # Tailwind + design system
└── app.html              # Base HTML template
```

## 🔐 Authentication

**Completely secure** authentication system integrated with backend:

### Features

- **JWT RS256** with automatic refresh
- **Svelte stores** for state management
- **Route protection** automatic
- **Token persistence** in localStorage
- **Auto-redirect** on token expiration

### Usage

```typescript
import { authStore, isAuthenticated, currentUser } from "$lib/auth/auth.store";

// Login
await authStore.login(username, password);

// Logout
await authStore.logout();

// Check auth status
$isAuthenticated; // true/false
$currentUser; // User object
```

## 🤖 AI Agents Integration

Chat interface for all **41+ real agents**:

### Features

- **Dynamic agent list** from backend
- **Modern chat interface** with history
- **Real-time execution tracking**
- **Robust error handling**
- **Mobile-friendly responsive design**

### Components

- `routes/(app)/agents/+page.svelte` - Main agents page
- Dynamic agent list with metadata
- Chat interface with typing indicators
- History management with localStorage

## 🎨 Design System

Design system based on **Tailwind CSS** with custom theme:

### Colors

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

### CSS Components

```css
/* Buttons */
.btn, .btn-primary, .btn-secondary, .btn-outline, .btn-ghost

/* Forms */
.input, .card, .badge

/* Layout */
.card, .card-header, .card-content, .card-footer
```

### Dark Mode

Complete dark mode support with:

- Custom CSS properties classes
- Automatic system theme toggle
- User preference persistence

## 📱 Responsive Design

**Mobile-first** design with breakpoints:

```css
sm: 640px   # Smartphone landscape
md: 768px   # Tablet
lg: 1024px  # Desktop
xl: 1280px  # Large desktop
```

### Navigation

- **Desktop**: Horizontal menu with user dropdown
- **Mobile**: Hamburger menu with overlay
- **Tablet**: Automatic adaptive layout

## 🔗 API Integration

Unified API client for backend communication:

### Features

- **Automatic auth headers** with JWT
- **Centralized error handling**
- **Request/response interceptors**
- **Timeout management**
- **Retry logic** on network failures

### Usage

```typescript
import { api } from "$lib/api-client";

// Agents
const agents = await api.getAgents();
const result = await api.executeAgent("ali-chief-of-staff", "Hello");

// Vector search
const docs = await api.searchDocuments("search query");

// Analytics
const dashboard = await api.getDashboard("7d");
const metrics = await api.getMetrics();
```

## 🧪 Testing

Complete testing setup:

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

### Available Scripts

```bash
npm run dev           # Dev server (port 4000)
npm run build         # Production build
npm run preview       # Preview build
npm run check         # Type checking
npm run lint          # ESLint + Prettier
npm run format        # Auto-format code
```

### Environment Variables

```bash
# .env.local
VITE_API_URL=http://localhost:9000
VITE_ENV=development
```

### Proxy Configuration

Dev server configured for automatic API proxy:

```typescript
// vite.config.ts
server: {
  proxy: {
    '/api': 'http://localhost:9000',
    '/health': 'http://localhost:9000'
  }
}
```

### Build & Deploy

#### Development

```bash
npm run dev
# Open http://localhost:4000
```

#### Production Build

```bash
npm run build
npm run preview
```

> **Note:** Docker is no longer supported or required. For deployment, use Azure Static Web Apps or App Service as described in the deployment documentation.

## 📊 Performance

### Bundle Size

- **Main bundle**: ~150KB gzipped
- **Vendor chunks**: Automatically separated
- **Code splitting**: Automatic route-based
- **Tree shaking**: Automatic optimization

### Lighthouse Score

Production targets:

- **Performance**: 90+
- **Accessibility**: 95+
- **Best Practices**: 90+
- **SEO**: 90+

## 🔒 Security

### Security Headers

```typescript
// hooks.server.ts
response.headers.set("X-Frame-Options", "DENY");
response.headers.set("X-Content-Type-Options", "nosniff");
response.headers.set("Referrer-Policy", "strict-origin-when-cross-origin");
```

### Content Security Policy

```html
<!-- Automatic CSP in production -->
script-src 'self'; style-src 'self' 'unsafe-inline'
https://fonts.googleapis.com; connect-src 'self' http://localhost:9000;
```

### Auth Security

- **JWT validation** on every request
- **Auto-logout** on token expiration
- **Secure storage** with TTL
- **CSRF protection** built-in SvelteKit

## 🎯 Main Features

### ✅ Implemented

- 🔐 **Complete JWT authentication**
- 🏠 **Dashboard with real-time metrics**
- 🤖 **Chat with 41+ real AI agents**
- 🔍 **Vector search interface**
- 📊 **Analytics and cost management**
- 📱 **Responsive design**
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

**Modern, secure and performant frontend for Convergio** 🚀
