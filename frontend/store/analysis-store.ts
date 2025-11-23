// store/analysis-store.ts
import { create } from "zustand";
import { devtools, persist } from "zustand/middleware";
import { apiClient, AnalysisResponse, AnalysisResult } from "@/lib/api";
import { cacheManager } from "@/lib/cache";

interface AnalysisState {
  // Current analysis session
  currentSession: AnalysisResponse | null;
  currentResult: AnalysisResult | null;
  
  // Session list
  sessions: any[];
  isLoadingSessions: boolean;
  
  // Cache stats
  cacheStats: any | null;
  cachePerformance: any | null;
  
  // Monitoring data
  agentPerformance: any | null;
  guardrailStats: any | null;
  geminiUsage: any | null;
  
  // Actions
  triggerAnalysis: (weekNumber: number, analysisType?: string, userId?: string) => Promise<AnalysisResponse>;
  getAnalysisStatus: (sessionId: string) => Promise<AnalysisResponse>;
  getAnalysisResult: (sessionId: string) => Promise<AnalysisResult>;
  fetchSessions: (forceRefresh?: boolean) => Promise<void>;
  fetchCacheStats: (forceRefresh?: boolean) => Promise<void>;
  fetchCachePerformance: (forceRefresh?: boolean) => Promise<void>;
  fetchAgentPerformance: (forceRefresh?: boolean) => Promise<void>;
  fetchGuardrailStats: (forceRefresh?: boolean) => Promise<void>;
  fetchGeminiUsage: (forceRefresh?: boolean) => Promise<void>;
  clearCache: () => Promise<void>;
  setCurrentSession: (session: AnalysisResponse | null) => void;
  setCurrentResult: (result: AnalysisResult | null) => void;
}

export const useAnalysisStore = create<AnalysisState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        currentSession: null,
        currentResult: null,
        sessions: [],
        isLoadingSessions: false,
        cacheStats: null,
        cachePerformance: null,
        agentPerformance: null,
        guardrailStats: null,
        geminiUsage: null,

        // Trigger analysis
        triggerAnalysis: async (weekNumber, analysisType = "comprehensive", userId = "current_user") => {
          try {
            const response = await apiClient.triggerAnalysis({
              week_number: weekNumber,
              analysis_type: analysisType as any,
              user_id: userId,
            });
            set({ currentSession: response });
            return response;
          } catch (error) {
            throw error;
          }
        },

        // Get analysis status
        getAnalysisStatus: async (sessionId) => {
          try {
            const response = await apiClient.getAnalysisStatus(sessionId);
            set({ currentSession: response });
            return response;
          } catch (error) {
            throw error;
          }
        },

        // Get analysis result
        getAnalysisResult: async (sessionId) => {
          try {
            const result = await apiClient.getAnalysisResult(sessionId);
            set({ currentResult: result });
            return result;
          } catch (error) {
            throw error;
          }
        },

        // Fetch sessions
        fetchSessions: async (forceRefresh = false) => {
          set({ isLoadingSessions: true });
          try {
            const response = await apiClient.getSessions(forceRefresh);
            // Response should have sessions array
            const sessions = response?.sessions || response || [];
            set({ sessions, isLoadingSessions: false });
            return response; // Return the response for use in components
          } catch (error) {
            set({ isLoadingSessions: false });
            throw error;
          }
        },

        // Fetch cache stats
        fetchCacheStats: async (forceRefresh = false) => {
          try {
            const stats = await apiClient.getCacheStats(forceRefresh);
            set({ cacheStats: stats });
          } catch (error) {
            throw error;
          }
        },

        // Fetch cache performance
        fetchCachePerformance: async (forceRefresh = false) => {
          try {
            const performance = await apiClient.getCachePerformance(forceRefresh);
            set({ cachePerformance: performance });
          } catch (error) {
            throw error;
          }
        },

        // Fetch agent performance
        fetchAgentPerformance: async (forceRefresh = false) => {
          try {
            const performance = await apiClient.getAgentPerformance(forceRefresh);
            set({ agentPerformance: performance });
          } catch (error) {
            throw error;
          }
        },

        // Fetch guardrail stats
        fetchGuardrailStats: async (forceRefresh = false) => {
          try {
            const stats = await apiClient.getGuardrailStats(forceRefresh);
            set({ guardrailStats: stats });
          } catch (error) {
            throw error;
          }
        },

        // Fetch Gemini usage
        fetchGeminiUsage: async (forceRefresh = false) => {
          try {
            const usage = await apiClient.getGeminiUsage(forceRefresh);
            set({ geminiUsage: usage });
          } catch (error) {
            throw error;
          }
        },

        // Clear cache
        clearCache: async () => {
          try {
            await apiClient.clearCache();
            // Clear local cache
            cacheManager.clear();
            // Reset cache-related state
            set({
              cacheStats: null,
              cachePerformance: null,
            });
          } catch (error) {
            throw error;
          }
        },

        // Set current session
        setCurrentSession: (session) => {
          set({ currentSession: session });
        },

        // Set current result
        setCurrentResult: (result) => {
          set({ currentResult: result });
        },
      }),
      {
        name: "analysis-storage",
        partialize: (state) => ({
          // Only persist certain fields
          currentSession: state.currentSession,
          currentResult: state.currentResult,
        }),
      }
    ),
    { name: "AnalysisStore" }
  )
);

