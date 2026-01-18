import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface ConceptNode {
  id: string;
  label: string;
  discipline: string;
  definition: string;
  credibility: number;
}

export interface ConceptEdge {
  source: string;
  target: string;
  relation: string;
  weight: number;
  reasoning: string;
}

export interface DiscoverResponse {
  status: string;
  request_id: string;
  data: {
    nodes: ConceptNode[];
    edges: ConceptEdge[];
    metadata: any;
  };
}

export interface GraphResponse {
  status: string;
  data: {
    nodes: ConceptNode[];
    edges: ConceptEdge[];
  };
}

export const conceptAPI = {
  /**
   * 概念挖掘接口
   */
  discover: async (concept: string, disciplines?: string[]) => {
    const response = await apiClient.post<DiscoverResponse>('/discover', {
      concept,
      disciplines,
      depth: 2,
      max_concepts: 30
    });
    return response.data;
  },

  /**
   * 查询图谱数据
   */
  getGraph: async (conceptId: string) => {
    const response = await apiClient.get<GraphResponse>(`/graph/${conceptId}`);
    return response.data;
  },

  /**
   * 搜索概念
   */
  searchConcepts: async (keyword: string, limit: number = 10) => {
    const response = await apiClient.get('/concepts/search', {
      params: { keyword, limit }
    });
    return response.data;
  },

  /**
   * 获取学科列表
   */
  getDisciplines: async () => {
    const response = await apiClient.get('/disciplines');
    return response.data;
  }
};
