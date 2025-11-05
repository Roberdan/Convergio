"use client"

import { Activity, Bot, Settings, User } from "lucide-react"
import Link from "next/link"

export function DashboardHeader() {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between">
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2">
            <Bot className="h-6 w-6 text-primary" />
            <span className="text-xl font-bold">Convergio</span>
          </Link>

          <nav className="hidden md:flex items-center gap-6">
            <Link
              href="/"
              className="text-sm font-medium transition-colors hover:text-primary"
            >
              Dashboard
            </Link>
            <Link
              href="/agents"
              className="text-sm font-medium text-muted-foreground transition-colors hover:text-primary"
            >
              Agents
            </Link>
            <Link
              href="/workflows"
              className="text-sm font-medium text-muted-foreground transition-colors hover:text-primary"
            >
              Workflows
            </Link>
            <Link
              href="/activity"
              className="text-sm font-medium text-muted-foreground transition-colors hover:text-primary"
            >
              Activity
            </Link>
          </nav>
        </div>

        <div className="flex items-center gap-4">
          <button
            className="flex h-9 w-9 items-center justify-center rounded-md border border-input bg-transparent hover:bg-accent hover:text-accent-foreground"
            aria-label="Activity"
          >
            <Activity className="h-4 w-4" />
          </button>

          <button
            className="flex h-9 w-9 items-center justify-center rounded-md border border-input bg-transparent hover:bg-accent hover:text-accent-foreground"
            aria-label="Settings"
          >
            <Settings className="h-4 w-4" />
          </button>

          <button
            className="flex h-9 w-9 items-center justify-center rounded-md border border-input bg-transparent hover:bg-accent hover:text-accent-foreground"
            aria-label="User profile"
          >
            <User className="h-4 w-4" />
          </button>
        </div>
      </div>
    </header>
  )
}
