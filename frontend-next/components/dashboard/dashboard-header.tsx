"use client"

import { Activity, Bot, Sparkles, User, Zap } from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"

export function DashboardHeader() {
  const pathname = usePathname()

  const isActive = (path: string) => pathname === path

  return (
    <header className="sticky top-0 z-50 w-full glass-header">
      <div className="container mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-r from-primary to-[hsl(var(--gradient-end))] rounded-xl blur-lg opacity-75 group-hover:opacity-100 transition-opacity"></div>
            <div className="relative bg-gradient-to-br from-primary to-[hsl(var(--gradient-end))] p-2 rounded-xl">
              <Bot className="h-5 w-5 text-white" />
            </div>
          </div>
          <div>
            <h1 className="text-xl font-bold gradient-text">Convergio</h1>
            <p className="text-[10px] text-muted-foreground -mt-0.5">Agent Framework</p>
          </div>
        </Link>

        {/* Navigation */}
        <nav className="hidden md:flex items-center gap-1">
          <NavLink href="/" active={isActive("/")}>
            <Sparkles className="h-4 w-4" />
            Dashboard
          </NavLink>
          <NavLink href="/agents" active={isActive("/agents")}>
            <Bot className="h-4 w-4" />
            Agents
          </NavLink>
          <NavLink href="/workflows" active={isActive("/workflows")}>
            <Zap className="h-4 w-4" />
            Workflows
          </NavLink>
          <NavLink href="/activity" active={isActive("/activity")}>
            <Activity className="h-4 w-4" />
            Activity
          </NavLink>
        </nav>

        {/* Actions */}
        <div className="flex items-center gap-3">
          {/* Status indicator */}
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-success/10 border border-success/20">
            <div className="w-2 h-2 rounded-full pulse-success"></div>
            <span className="text-xs font-medium text-success">Online</span>
          </div>

          {/* User menu */}
          <button className="group flex items-center justify-center w-9 h-9 rounded-full bg-gradient-to-br from-primary/20 to-[hsl(var(--gradient-end))]/10 border border-white/10 hover:border-white/20 transition-all hover:scale-105">
            <User className="h-4 w-4 text-primary" />
          </button>
        </div>
      </div>
    </header>
  )
}

function NavLink({
  href,
  active,
  children,
}: {
  href: string
  active: boolean
  children: React.ReactNode
}) {
  return (
    <Link
      href={href}
      className={cn(
        "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all",
        active
          ? "bg-primary/10 text-primary border border-primary/20"
          : "text-muted-foreground hover:text-foreground hover:bg-white/5"
      )}
    >
      {children}
    </Link>
  )
}
