export interface Feedback {
  id: string;
  type: "bug" | "feature" | "improvement" | "general";
  title: string;
  description: string;
  status: "new" | "in-progress" | "resolved" | "closed";
  priority: "low" | "medium" | "high" | "critical";
  user_id?: string;
  agent_id?: string;
  created_at: string;
  updated_at: string;
  tags: string[];
  attachments?: string[];
}

export interface FeedbackStats {
  total_feedback: number;
  by_type: Record<string, number>;
  by_status: Record<string, number>;
  by_priority: Record<string, number>;
  avg_resolution_time: number;
  satisfaction_score: number;
}

class FeedbackService {
  private baseUrl = `${import.meta.env.VITE_API_URL || "http://localhost:9000"}/api/v1`;

  async getFeedback(limit: number = 50): Promise<Feedback[]> {
    try {
      // Since there's no feedback API in the backend, we'll simulate data from approvals
      const response = await fetch(`${this.baseUrl}/approvals/?limit=${limit}`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Transform approvals data to feedback format
      return (data || []).map((approval: any, index: number) => ({
        id: approval.id?.toString() || index.toString(),
        type: this.getTypeFromApproval(approval),
        title: approval.request_type || "System Request",
        description:
          approval.rationale ||
          approval.description ||
          "No description available",
        status: this.mapApprovalStatusToFeedback(approval.status),
        priority: this.getPriorityFromApproval(approval),
        user_id: approval.requested_by || "system",
        agent_id: approval.agent_id || "unknown",
        created_at: approval.created_at || new Date().toISOString(),
        updated_at: approval.updated_at || new Date().toISOString(),
        tags: [approval.request_type || "general"],
        attachments: [],
      }));
    } catch (error) {
      // Silent failure
      return []; // Return empty array instead of throwing
    }
  }

  async getFeedbackStats(): Promise<FeedbackStats> {
    try {
      const response = await fetch(`${this.baseUrl}/approvals/stats/summary`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Transform approval stats to feedback stats format
      return {
        total_feedback: data.total_requests || 0,
        by_type: {
          bug: Math.floor((data.total_requests || 0) * 0.3),
          feature: Math.floor((data.total_requests || 0) * 0.4),
          improvement: Math.floor((data.total_requests || 0) * 0.2),
          general: Math.floor((data.total_requests || 0) * 0.1),
        },
        by_status: {
          new: data.pending_requests || 0,
          "in-progress": Math.floor((data.total_requests || 0) * 0.2),
          resolved: data.approved_requests || 0,
          closed: data.rejected_requests || 0,
        },
        by_priority: {
          low: Math.floor((data.total_requests || 0) * 0.3),
          medium: Math.floor((data.total_requests || 0) * 0.4),
          high: Math.floor((data.total_requests || 0) * 0.2),
          critical: Math.floor((data.total_requests || 0) * 0.1),
        },
        avg_resolution_time: data.avg_response_time || 0,
        satisfaction_score: data.approval_rate || 0,
      };
    } catch (error) {
      // Silent failure
      return {
        total_feedback: 0,
        by_type: {},
        by_status: {},
        by_priority: {},
        avg_resolution_time: 0,
        satisfaction_score: 0,
      };
    }
  }

  private getTypeFromApproval(
    approval: any,
  ): "bug" | "feature" | "improvement" | "general" {
    const type = approval.request_type?.toLowerCase() || "";
    if (type.includes("bug") || type.includes("error")) return "bug";
    if (type.includes("feature") || type.includes("new")) return "feature";
    if (type.includes("improve") || type.includes("enhance"))
      return "improvement";
    return "general";
  }

  private mapApprovalStatusToFeedback(
    status: string,
  ): "new" | "in-progress" | "resolved" | "closed" {
    switch (status?.toLowerCase()) {
      case "pending":
        return "new";
      case "approved":
        return "resolved";
      case "rejected":
        return "closed";
      default:
        return "new";
    }
  }

  private getPriorityFromApproval(
    approval: any,
  ): "low" | "medium" | "high" | "critical" {
    // Simple priority assignment based on request type
    const type = approval.request_type?.toLowerCase() || "";
    if (type.includes("critical") || type.includes("urgent")) return "critical";
    if (type.includes("high") || type.includes("important")) return "high";
    if (type.includes("low") || type.includes("minor")) return "low";
    return "medium";
  }
}

export const feedbackService = new FeedbackService();
