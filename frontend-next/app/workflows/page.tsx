import { DashboardHeader } from "@/components/dashboard/dashboard-header"
import { GitBranch, Play, Pause, MoreVertical } from "lucide-react"

export default function WorkflowsPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <DashboardHeader />

      <main className="flex-1 space-y-6 p-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Workflows</h1>
            <p className="text-muted-foreground mt-2">
              Orchestration patterns and execution history
            </p>
          </div>

          <button className="inline-flex h-10 items-center justify-center rounded-md bg-primary px-6 text-sm font-medium text-primary-foreground hover:bg-primary/90">
            Create Workflow
          </button>
        </div>

        <div className="grid gap-4">
          {getMockWorkflows().map((workflow) => (
            <div
              key={workflow.id}
              className="rounded-lg border bg-card p-6 shadow-sm hover:shadow-md transition-all"
            >
              <div className="flex items-start justify-between">
                <div className="flex gap-4">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                    <GitBranch className="h-6 w-6 text-primary" />
                  </div>

                  <div>
                    <h3 className="font-semibold text-lg mb-1">{workflow.name}</h3>
                    <p className="text-sm text-muted-foreground mb-3">
                      {workflow.description}
                    </p>

                    <div className="flex gap-4 text-sm">
                      <span className="text-muted-foreground">
                        <span className="font-medium">{workflow.agents}</span> agents
                      </span>
                      <span className="text-muted-foreground">
                        <span className="font-medium">{workflow.executions}</span> executions
                      </span>
                      <span className="text-muted-foreground">
                        Last run: <span className="font-medium">{workflow.lastRun}</span>
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex gap-2">
                  <button className="flex h-9 w-9 items-center justify-center rounded-md border hover:bg-accent">
                    {workflow.status === 'active' ? (
                      <Pause className="h-4 w-4" />
                    ) : (
                      <Play className="h-4 w-4" />
                    )}
                  </button>
                  <button className="flex h-9 w-9 items-center justify-center rounded-md border hover:bg-accent">
                    <MoreVertical className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  )
}

function getMockWorkflows() {
  return [
    {
      id: "1",
      name: "Multi-Agent Research",
      description: "Parallel research workflow with synthesis",
      agents: 5,
      executions: 142,
      lastRun: "2 hours ago",
      status: "active",
    },
    {
      id: "2",
      name: "Code Review Pipeline",
      description: "Automated code review and testing",
      agents: 3,
      executions: 89,
      lastRun: "5 hours ago",
      status: "active",
    },
    {
      id: "3",
      name: "Data Analysis",
      description: "Sequential data processing and visualization",
      agents: 4,
      executions: 67,
      lastRun: "1 day ago",
      status: "inactive",
    },
  ]
}
