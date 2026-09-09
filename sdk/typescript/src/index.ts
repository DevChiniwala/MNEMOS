export interface MnemosConfig {
  apiKey?: string;
  baseUrl?: string;
}

export interface MemorizeRequest {
  text: string;
  userId?: string;
  metadata?: Record<string, any>;
}

export interface ResearchRequest {
  question: string;
  userId?: string;
  maxIters?: number;
}

export class MnemosClient {
  private baseUrl: string;
  private apiKey: string;

  constructor(config?: MnemosConfig) {
    this.baseUrl = config?.baseUrl || 'http://localhost:8000/v1';
    this.apiKey = config?.apiKey || '';
  }

  private get headers(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }
    return headers;
  }

  /**
   * Stores a fact into the memory system.
   */
  async memorize(request: MemorizeRequest): Promise<any> {
    const response = await fetch(`${this.baseUrl}/memories`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({
        text: request.text,
        user_id: request.userId || 'default',
        metadata: request.metadata || {}
      })
    });

    if (!response.ok) {
      throw new Error(`MNEMOS Error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Performs an iterative research loop across memory.
   */
  async research(request: ResearchRequest): Promise<{ answer: string; sources: string[] }> {
    const response = await fetch(`${this.baseUrl}/research`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({
        question: request.question,
        user_id: request.userId || 'default',
        max_iters: request.maxIters || 3
      })
    });

    if (!response.ok) {
      throw new Error(`MNEMOS Error: ${response.statusText}`);
    }

    return response.json();
  }
}
