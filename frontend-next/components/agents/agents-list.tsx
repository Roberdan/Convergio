"use client"

import { useQuery } from "@tanstack/react-query"
import { Bot, ChevronRight } from "lucide-react"
import Link from "next/link"

interface Agent {
  key: string
  name: string
  description: string
  tier: number
  expertise_keywords: string[]
  status: "active" | "inactive"
}

async function fetchAgents(): Promise<Agent[]> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:9000'
  const response = await fetch(`${apiUrl}/api/v1/agents`, {
    headers: { 'Content-Type': 'application/json' },
  })

  if (!response.ok) {
    throw new Error('Failed to fetch agents')
  }

  const data = await response.json()
  return data.agents || []
}

export function AgentsList() {
  const { data: agents, isLoading, error } = useQuery({
    queryKey: ['agents'],
    queryFn: fetchAgents,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  return (
    <div className="rounded-lg border bg-card p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">AI Agents</h3>
        <Link
          href="/agents"
          className="text-sm text-primary hover:underline flex items-center gap-1"
        >
          View all
          <ChevronRight className="h-4 w-4" />
        </Link>
      </div>

      {error && (
        <div className="text-sm text-destructive">
          Failed to load agents. Using fallback data.
        </div>
      )}

      <div className="space-y-3">
        {isLoading ? (
          <>
            {[...Array(5)].map((_, i) => (
              <div key={i} className="animate-pulse flex items-center gap-3 p-3 rounded-lg">
                <div className="h-10 w-10 bg-muted rounded-full"></div>
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-muted rounded w-1/3"></div>
                  <div className="h-3 bg-muted rounded w-2/3"></div>
                </div>
              </div>
            ))}
          </>
        ) : (
          <>
            {(agents || getMockAgents()).slice(0, 5).map((agent) => (
              <Link
                key={agent.key}
                href={`/agents/${agent.key}`}
                className="flex items-center gap-3 p-3 rounded-lg border hover:bg-accent/50 transition-colors"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
                  <Bot className="h-5 w-5 text-primary" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">{agent.name}</p>
                  <p className="text-sm text-muted-foreground truncate">
                    {agent.description}
                  </p>
                </div>
                <div className={`h-2 w-2 rounded-full ${
                  agent.status === 'active' ? 'bg-green-500' : 'bg-gray-400'
                }`}></div>
              </Link>
            ))}
          </>
        )}
      </div>
    </div>
  )
}

function getMockAgents(): Agent[] {
  return [
    {
      key: "ali_chief_of_staff",
      name: "Ali - Chief of Staff",
      description: "Master orchestrator and coordinator",
      tier: 1,
      expertise_keywords: ["orchestration", "coordination", "strategy"],
      status: "active",
    },
    {
      key: "dev_ops_specialist",
      name: "DevOps Specialist",
      description: "Cloud infrastructure and deployment expert",
      tier: 2,
      expertise_keywords: ["aws", "docker", "kubernetes"],
      status: "active",
    },
    {
      key: "data_analyst",
      name: "Data Analyst",
      description: "Advanced analytics and insights",
      tier: 2,
      expertise_keywords: ["analytics", "sql", "visualization"],
      status: "active",
    },
    {
      key: "frontend_specialist",
      name: "Frontend Specialist",
      description: "React and Next.js expert",
      tier: 2,
      expertise_keywords: ["react", "nextjs", "typescript"],
      status: "active",
    },
    {
      key: "backend_architect",
      name: "Backend Architect",
      description: "API design and system architecture",
      tier: 2,
      expertise_keywords: ["python", "fastapi", "architecture"],
      status: "active",
    },
  ]
}
