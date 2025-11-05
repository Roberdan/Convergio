"use client"

import { useQuery } from "@tanstack/react-query"
import { MessageSquare, CheckCircle2, AlertCircle, Clock } from "lucide-react"
import { formatDistanceToNow } from "@/lib/date-utils"

interface Activity {
  id: string
  type: "message" | "workflow" | "error"
  agent: string
  description: string
  timestamp: string
  status: "success" | "pending" | "error"
}

async function fetchActivity(): Promise<Activity[]> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:9000'
  const response = await fetch(`${apiUrl}/api/v1/activity/recent`, {
    headers: { 'Content-Type': 'application/json' },
  })

  if (!response.ok) {
    throw new Error('Failed to fetch activity')
  }

  const data = await response.json()
  return data.activity || []
}

export function RecentActivity() {
  const { data: activity, isLoading, error } = useQuery({
    queryKey: ['recent-activity'],
    queryFn: fetchActivity,
    refetchInterval: 10000, // Refetch every 10 seconds
  })

  const activities = error ? getMockActivity() : (activity || getMockActivity())

  return (
    <div className="rounded-lg border bg-card p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Recent Activity</h3>
        <button className="text-sm text-primary hover:underline">
          View all
        </button>
      </div>

      <div className="space-y-4">
        {isLoading ? (
          <>
            {[...Array(5)].map((_, i) => (
              <div key={i} className="animate-pulse flex gap-3">
                <div className="h-10 w-10 bg-muted rounded-full"></div>
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-muted rounded w-2/3"></div>
                  <div className="h-3 bg-muted rounded w-1/2"></div>
                </div>
              </div>
            ))}
          </>
        ) : (
          <>
            {activities.slice(0, 5).map((item) => (
              <ActivityItem key={item.id} activity={item} />
            ))}
          </>
        )}
      </div>
    </div>
  )
}

function ActivityItem({ activity }: { activity: Activity }) {
  const getIcon = () => {
    switch (activity.status) {
      case "success":
        return <CheckCircle2 className="h-5 w-5 text-green-500" />
      case "error":
        return <AlertCircle className="h-5 w-5 text-destructive" />
      case "pending":
        return <Clock className="h-5 w-5 text-yellow-500" />
      default:
        return <MessageSquare className="h-5 w-5 text-primary" />
    }
  }

  return (
    <div className="flex gap-3">
      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted">
        {getIcon()}
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-medium text-sm">{activity.agent}</p>
        <p className="text-sm text-muted-foreground truncate">
          {activity.description}
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          {formatDistanceToNow(activity.timestamp)}
        </p>
      </div>
    </div>
  )
}

function getMockActivity(): Activity[] {
  const now = new Date()
  return [
    {
      id: "1",
      type: "message",
      agent: "Ali - Chief of Staff",
      description: "Orchestrated multi-agent workflow for user query",
      timestamp: new Date(now.getTime() - 2 * 60000).toISOString(),
      status: "success",
    },
    {
      id: "2",
      type: "workflow",
      agent: "DevOps Specialist",
      description: "Deployed application to production",
      timestamp: new Date(now.getTime() - 15 * 60000).toISOString(),
      status: "success",
    },
    {
      id: "3",
      type: "message",
      agent: "Data Analyst",
      description: "Generated analytics report",
      timestamp: new Date(now.getTime() - 30 * 60000).toISOString(),
      status: "success",
    },
    {
      id: "4",
      type: "error",
      agent: "Backend Architect",
      description: "API endpoint timeout",
      timestamp: new Date(now.getTime() - 45 * 60000).toISOString(),
      status: "error",
    },
    {
      id: "5",
      type: "workflow",
      agent: "Frontend Specialist",
      description: "Processing user interface update",
      timestamp: new Date(now.getTime() - 60 * 60000).toISOString(),
      status: "pending",
    },
  ]
}
