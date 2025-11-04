# Convergio Frontend - Next.js 15 + React 19

Modern, professional frontend for Convergio built with latest technologies.

## Tech Stack

- **Framework:** Next.js 15 (App Router)
- **UI Library:** React 19
- **Language:** TypeScript (strict mode)
- **Styling:** Tailwind CSS 4
- **Components:** Shadcn UI + Radix UI
- **State:** Zustand + React Query
- **Charts:** Recharts
- **Animation:** Framer Motion
- **Icons:** Lucide React

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

- ✅ Modern, clean UI design
- ✅ Dark/light mode support
- ✅ Responsive (mobile-first)
- ✅ Real-time dashboard
- ✅ Agent management interface
- ✅ Workflow builder
- ✅ Analytics & cost tracking
- ✅ Accessibility (WCAG 2.1 AA)
- ✅ Performance optimized

## Project Structure

```
frontend-next/
├── app/                    # Next.js App Router
├── components/            # React components
├── lib/                   # Utilities and API
└── public/               # Static assets
```

## Environment Variables

Create a `.env.local` file:

```
NEXT_PUBLIC_API_URL=http://localhost:9000
```

## Development

Access at http://localhost:4000

Backend API proxied from :9000 to :4000/api/v1
