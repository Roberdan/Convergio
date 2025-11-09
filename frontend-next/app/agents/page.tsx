import { Suspense } from "react"
import { DashboardHeader } from "@/components/dashboard/dashboard-header"
import { Bot, Search } from "lucide-react"

export default function AgentsPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <DashboardHeader />

      <main className="flex-1 space-y-6 p-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">AI Agents</h1>
            <p className="text-muted-foreground mt-2">
              Manage and monitor all 48 specialist agents
            </p>
          </div>

          <button className="inline-flex h-10 items-center justify-center rounded-md bg-primary px-6 text-sm font-medium text-primary-foreground hover:bg-primary/90">
            Add Agent
          </button>
        </div>

        <div className="flex gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              type="search"
              placeholder="Search agents..."
              className="h-10 w-full rounded-md border border-input bg-background pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>

          <select className="h-10 rounded-md border border-input bg-background px-4 text-sm focus:outline-none focus:ring-2 focus:ring-ring">
            <option>All Tiers</option>
            <option>Tier 1</option>
            <option>Tier 2</option>
            <option>Tier 3</option>
          </select>

          <select className="h-10 rounded-md border border-input bg-background px-4 text-sm focus:outline-none focus:ring-2 focus:ring-ring">
            <option>All Status</option>
            <option>Active</option>
            <option>Inactive</option>
          </select>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {getMockAgents().map((agent) => (
            <a
              key={agent.key}
              href={`/agents/${agent.key}`}
              className="group rounded-lg border bg-card p-6 shadow-sm hover:shadow-md transition-all"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                  <Bot className="h-6 w-6 text-primary" />
                </div>
                <div className={`h-2 w-2 rounded-full ${
                  agent.status === 'active' ? 'bg-green-500' : 'bg-gray-400'
                }`}></div>
              </div>

              <h3 className="font-semibold text-lg mb-2 group-hover:text-primary transition-colors">
                {agent.name}
              </h3>
              <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
                {agent.description}
              </p>

              <div className="flex flex-wrap gap-2">
                {agent.expertise_keywords.slice(0, 3).map((keyword) => (
                  <span
                    key={keyword}
                    className="px-2 py-1 text-xs rounded-full bg-secondary text-secondary-foreground"
                  >
                    {keyword}
                  </span>
                ))}
              </div>
            </a>
          ))}
        </div>
      </main>
    </div>
  )
}

function getMockAgents() {
  const keywords = [
    ['typescript', 'react', 'nextjs'],
    ['python', 'fastapi', 'sqlalchemy'],
    ['aws', 'docker', 'kubernetes'],
    ['analytics', 'sql', 'visualization'],
    ['design', 'figma', 'ui/ux'],
  ]

  return Array.from({ length: 12 }, (_, i) => ({
    key: `agent_${i}`,
    name: `Agent ${i + 1}`,
    description: `Specialist agent for ${['development', 'design', 'analytics', 'operations'][i % 4]}`,
    tier: (i % 3) + 1,
    expertise_keywords: keywords[i % 5],
    status: i % 4 === 0 ? 'inactive' : 'active',
  }))
}
