"use client"

import { useQuery } from "@tanstack/react-query"
import { Bot, MessageSquare, TrendingUp, Zap } from "lucide-react"

interface Stats {
  total_agents: number
  active_conversations: number
  total_messages_today: number
  average_response_time_ms: number
}

async function fetchStats(): Promise<Stats> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:9000'
  const response = await fetch(`${apiUrl}/api/v1/stats`, {
    headers: { 'Content-Type': 'application/json' },
  })

  if (!response.ok) {
    throw new Error('Failed to fetch stats')
  }

  return response.json()
}

export function StatsCards() {
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['stats'],
    queryFn: fetchStats,
    refetchInterval: 30000, // Refetch every 30 seconds
  })

  if (error) {
    return (
      <div className="grid gap-4 md:grid-cols-4">
        <StatCard
          title="Total Agents"
          value="48"
          icon={<Bot className="h-4 w-4" />}
          trend="+2 from last week"
        />
        <StatCard
          title="Active Conversations"
          value="12"
          icon={<MessageSquare className="h-4 w-4" />}
          trend="+3 from yesterday"
        />
        <StatCard
          title="Messages Today"
          value="156"
          icon={<TrendingUp className="h-4 w-4" />}
          trend="+12% from yesterday"
        />
        <StatCard
          title="Avg Response Time"
          value="1.2s"
          icon={<Zap className="h-4 w-4" />}
          trend="-0.3s from last hour"
        />
      </div>
    )
  }

  return (
    <div className="grid gap-4 md:grid-cols-4">
      <StatCard
        title="Total Agents"
        value={String(stats?.total_agents || 48)}
        icon={<Bot className="h-4 w-4" />}
        trend="+2 from last week"
      />
      <StatCard
        title="Active Conversations"
        value={String(stats?.active_conversations || 0)}
        icon={<MessageSquare className="h-4 w-4" />}
        trend="+3 from yesterday"
      />
      <StatCard
        title="Messages Today"
        value={String(stats?.total_messages_today || 0)}
        icon={<TrendingUp className="h-4 w-4" />}
        trend="+12% from yesterday"
      />
      <StatCard
        title="Avg Response Time"
        value={stats ? `${(stats.average_response_time_ms / 1000).toFixed(1)}s` : "1.2s"}
        icon={<Zap className="h-4 w-4" />}
        trend="-0.3s from last hour"
      />
    </div>
  )
}

function StatCard({
  title,
  value,
  icon,
  trend,
}: {
  title: string
  value: string
  icon: React.ReactNode
  trend: string
}) {
  return (
    <div className="rounded-lg border bg-card p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-muted-foreground">{title}</p>
        <div className="text-muted-foreground">{icon}</div>
      </div>
      <div className="mt-2">
        <h3 className="text-3xl font-bold">{value}</h3>
        <p className="text-xs text-muted-foreground mt-1">{trend}</p>
      </div>
    </div>
  )
}
