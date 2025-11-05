import { Suspense } from "react"
import { DashboardHeader } from "@/components/dashboard/dashboard-header"
import { StatsCards } from "@/components/dashboard/stats-cards"
import { AgentsList } from "@/components/agents/agents-list"
import { RecentActivity } from "@/components/dashboard/recent-activity"

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col">
      <DashboardHeader />

      <main className="flex-1 space-y-8 p-8">
        <div>
          <h1 className="text-4xl font-bold tracking-tight">Convergio Dashboard</h1>
          <p className="text-muted-foreground mt-2">
            Orchestrate and monitor your AI agents powered by Microsoft Agent Framework
          </p>
        </div>

        <Suspense fallback={<StatsLoading />}>
          <StatsCards />
        </Suspense>

        <div className="grid gap-8 md:grid-cols-2">
          <Suspense fallback={<CardLoading />}>
            <AgentsList />
          </Suspense>

          <Suspense fallback={<CardLoading />}>
            <RecentActivity />
          </Suspense>
        </div>
      </main>
    </div>
  )
}

function StatsLoading() {
  return (
    <div className="grid gap-4 md:grid-cols-4">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="animate-pulse rounded-lg border bg-card p-6">
          <div className="h-4 bg-muted rounded w-1/2 mb-2"></div>
          <div className="h-8 bg-muted rounded w-3/4"></div>
        </div>
      ))}
    </div>
  )
}

function CardLoading() {
  return (
    <div className="animate-pulse rounded-lg border bg-card p-6">
      <div className="h-6 bg-muted rounded w-1/3 mb-4"></div>
      <div className="space-y-3">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-16 bg-muted rounded"></div>
        ))}
      </div>
    </div>
  )
}
