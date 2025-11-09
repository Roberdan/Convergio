# Convergio Frontend - Next.js 15 + React 19

Modern, professional frontend for Convergio AI Agent Platform powered by Microsoft Agent Framework.

## Tech Stack

- **Framework:** Next.js 15.1.0 (App Router)
- **UI Library:** React 19.0.0
- **Language:** TypeScript (strict mode)
- **Styling:** Tailwind CSS 3.4 with custom design system
- **State Management:** TanStack React Query + Zustand
- **Icons:** Lucide React
- **Utils:** clsx + tailwind-merge (cn helper)

## Getting Started

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

## Features

- ✅ **Dashboard:** Real-time stats, agent status, recent activity
- ✅ **Agent Management:** Browse and monitor all 48 specialist agents
- ✅ **Workflow Orchestration:** View and manage agent workflows
- ✅ **Activity Log:** Complete activity feed with filtering
- ✅ **Responsive Design:** Works on all devices
- ✅ **Dark Mode Support:** Via CSS variables
- ✅ **Real-time Updates:** Auto-refresh with React Query
- ✅ **Type-Safe:** Full TypeScript coverage
- ✅ **Performance:** Optimized with Next.js 15

## Project Structure

```
frontend-next/
├── app/
│   ├── page.tsx                 # Dashboard homepage
│   ├── agents/                  # Agent pages
│   ├── workflows/               # Workflow pages
│   ├── activity/                # Activity log
│   ├── layout.tsx               # Root layout
│   ├── providers.tsx            # React Query provider
│   └── globals.css              # Global styles + theme
├── components/
│   ├── dashboard/               # Dashboard components
│   ├── agents/                  # Agent components
│   └── ui/                      # Reusable UI components
├── lib/
│   ├── utils.ts                 # cn() helper
│   └── date-utils.ts            # Date formatting
├── tailwind.config.ts           # Tailwind configuration
├── next.config.ts               # Next.js configuration
└── tsconfig.json                # TypeScript configuration
```

## Environment Variables

Copy `.env.example` to `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:9000
NEXT_PUBLIC_WS_URL=ws://localhost:9000
```

## Development

1. Install dependencies: `npm install`
2. Start dev server: `npm run dev`
3. Access at: http://localhost:4000

The app connects to the backend API at http://localhost:9000
