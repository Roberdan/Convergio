import { DashboardHeader } from "@/components/dashboard/dashboard-header"
import { CheckCircle2, AlertCircle, Clock, MessageSquare } from "lucide-react"

export default function ActivityPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <DashboardHeader />

      <main className="flex-1 space-y-6 p-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Activity Log</h1>
          <p className="text-muted-foreground mt-2">
            Real-time feed of all agent activities and workflows
          </p>
        </div>

        <div className="flex gap-4">
          <select className="h-10 rounded-md border border-input bg-background px-4 text-sm focus:outline-none focus:ring-2 focus:ring-ring">
            <option>All Types</option>
            <option>Messages</option>
            <option>Workflows</option>
            <option>Errors</option>
          </select>

          <select className="h-10 rounded-md border border-input bg-background px-4 text-sm focus:outline-none focus:ring-2 focus:ring-ring">
            <option>Last 24 hours</option>
            <option>Last 7 days</option>
            <option>Last 30 days</option>
          </select>
        </div>

        <div className="space-y-4">
          {getMockActivity().map((item) => (
            <div
              key={item.id}
              className="rounded-lg border bg-card p-6 shadow-sm hover:shadow-md transition-all"
            >
              <div className="flex gap-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted">
                  {getStatusIcon(item.status)}
                </div>

                <div className="flex-1">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h4 className="font-semibold">{item.agent}</h4>
                      <p className="text-sm text-muted-foreground">{item.description}</p>
                    </div>
                    <span className="text-xs text-muted-foreground">{item.timestamp}</span>
                  </div>

                  {item.details && (
                    <div className="mt-3 rounded-md bg-muted/50 p-3">
                      <p className="text-sm font-mono">{item.details}</p>
                    </div>
                  )}

                  <div className="flex gap-4 mt-3 text-xs text-muted-foreground">
                    <span>Duration: {item.duration}</span>
                    <span>Cost: ${item.cost}</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  )
}

function getStatusIcon(status: string) {
  switch (status) {
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

function getMockActivity() {
  return [
    {
      id: "1",
      agent: "Ali - Chief of Staff",
      description: "Orchestrated multi-agent workflow for complex query",
      status: "success",
      timestamp: "2 minutes ago",
      duration: "3.2s",
      cost: "0.042",
      details: "Sequential execution: Data Analyst → Frontend Specialist → DevOps",
    },
    {
      id: "2",
      agent: "DevOps Specialist",
      description: "Deployed application to production environment",
      status: "success",
      timestamp: "15 minutes ago",
      duration: "45.1s",
      cost: "0.018",
      details: null,
    },
    {
      id: "3",
      agent: "Data Analyst",
      description: "Generated comprehensive analytics report",
      status: "success",
      timestamp: "1 hour ago",
      duration: "8.7s",
      cost: "0.031",
      details: null,
    },
    {
      id: "4",
      agent: "Backend Architect",
      description: "API endpoint timeout during heavy load",
      status: "error",
      timestamp: "2 hours ago",
      duration: "30.0s",
      cost: "0.015",
      details: "Error: Connection timeout after 30s. Retry recommended.",
    },
    {
      id: "5",
      agent: "Frontend Specialist",
      description: "Processing UI component generation",
      status: "pending",
      timestamp: "3 hours ago",
      duration: "ongoing",
      cost: "0.000",
      details: null,
    },
  ]
}
