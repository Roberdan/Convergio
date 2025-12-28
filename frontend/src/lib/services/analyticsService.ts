export interface AnalyticsData {
  activities: Activity[];
  performance: PerformanceData;
  trends: TrendData;
}

export interface Activity {
  id: string;
  type: string;
  description: string;
  timestamp: string;
  user_id?: string;
  metadata?: any;
}

export interface PerformanceData {
  response_times: number[];
  success_rates: number[];
  error_rates: number[];
  throughput: number[];
  timestamps: string[];
}

export interface TrendData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    color: string;
  }[];
}

class AnalyticsService {
  private baseUrl = `${import.meta.env.VITE_API_URL || "http://localhost:9000"}/api/v1`;

  async getActivities(limit: number = 50): Promise<Activity[]> {
    try {
      const response = await fetch(
        `${this.baseUrl}/analytics/activities?limit=${limit}`,
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.activities || [];
    } catch (error) {
      // Silent failure
      throw error;
    }
  }

  async getPerformanceMetrics(timeRange: string = "7d"): Promise<any> {
    try {
      const response = await fetch(
        `${this.baseUrl}/analytics/performance?time_range=${timeRange}`,
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      // Silent failure
      throw error;
    }
  }

  async getRealTimeData(): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/analytics/real-time`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      // Silent failure
      throw error;
    }
  }

  async exportData(
    format: "csv" | "json" = "json",
    timeRange: string = "7d",
  ): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/analytics/export`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          format,
          time_range: timeRange,
          include_metrics: true,
          include_activities: true,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      // Silent failure
      throw error;
    }
  }
}

export const analyticsService = new AnalyticsService();
