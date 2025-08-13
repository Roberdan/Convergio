export interface Workflow {
  workflow_id: string;
  name: string;
  description: string;
  category: string;
  complexity: string;
  estimated_duration: number;
  steps_count: number;
  agents_involved?: string[];
  business_domain?: string;
}

export interface WorkflowStep {
  id: string;
  name: string;
  type: string;
  configuration: any;
  order: number;
}

export interface WorkflowExecution {
  execution_id: string;
  workflow_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  started_at: string;
  completed_at?: string;
  duration_seconds?: number;
  result?: any;
  error_message?: string;
  current_step?: string;
  progress_percentage: number;
}

export interface RecentExecution {
  execution_id: string;
  workflow_name: string;
  status: string;
  started_at: string;
  duration: number;
  success_rate: number;
}

class WorkflowsService {
  private baseUrl = 'http://localhost:9000/api/v1';

  async getWorkflows(): Promise<Workflow[]> {
    try {
      const response = await fetch(`${this.baseUrl}/workflows/`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      return data.workflows || [];
    } catch (error) {
      console.error('Failed to fetch workflows:', error);
      throw error;
    }
  }

  async getWorkflowExecution(executionId: string): Promise<WorkflowExecution> {
    try {
      const response = await fetch(`${this.baseUrl}/workflows/execution/${executionId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch workflow execution:', error);
      throw error;
    }
  }

  async getRecentExecutions(): Promise<RecentExecution[]> {
    try {
      const response = await fetch(`${this.baseUrl}/workflows/executions/recent`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      return data.executions || [];
    } catch (error) {
      console.error('Failed to fetch recent executions:', error);
      throw error;
    }
  }

  async getWorkflowDetails(workflowId: string): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/workflows/${workflowId}/details`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch workflow details:', error);
      throw error;
    }
  }
  
  async executeWorkflow(workflowId: string, userRequest: string, userId: string = 'dashboard-user'): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/workflows/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workflow_id: workflowId,
          user_request: userRequest,
          user_id: userId
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Failed to execute workflow:', error);
      throw error;
    }
  }
}

export const workflowsService = new WorkflowsService();