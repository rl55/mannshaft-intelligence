// hooks/use-analysis-progress.ts
import { useEffect, useRef, useState, useCallback } from "react";
import { apiClient } from "@/lib/api";

// Construct WebSocket URL from API URL or use explicit WS URL
const getWebSocketURL = (): string => {
  if (process.env.NEXT_PUBLIC_WS_URL) {
    return process.env.NEXT_PUBLIC_WS_URL;
  }
  
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  // Convert http:// to ws:// and https:// to wss://
  return apiUrl.replace(/^http/, "ws");
};

const WS_BASE_URL = getWebSocketURL();

export interface AnalysisEvent {
  type:
    | "agent_started"
    | "agent_completed"
    | "agent_progress"
    | "guardrail_check"
    | "evaluation_complete"
    | "progress_update"
    | "error"
    | "analysis_failed"
    | "warning"
    | "retry"
    | "completed";
  progress: number;
  agent?: string;
  data?: any;
  timestamp?: number;
  message?: string;
  status?: string;
  is_transient?: boolean;
  can_retry?: boolean;
  error?: string;
  retry_attempt?: number;
  max_retries?: number;
}

interface UseAnalysisProgressOptions {
  autoReconnect?: boolean;
  reconnectDelay?: number;
  maxReconnectAttempts?: number;
  onComplete?: () => void;
  onError?: (error: Error) => void;
  onAnalysisFailed?: (message: string, canRetry: boolean) => void; // Called when analysis fails
  waitForSession?: boolean; // Wait for session to exist before connecting
  initialDelay?: number; // Delay before first connection attempt
}

export function useAnalysisProgress(
  sessionId: string | null,
  options: UseAnalysisProgressOptions = {}
) {
  const {
    autoReconnect = true,
    reconnectDelay = 3000,
    maxReconnectAttempts = 5,
    onComplete,
    onError,
    onAnalysisFailed,
    waitForSession = false, // Don't wait - connect immediately
    initialDelay = 0, // Connect IMMEDIATELY - no delay
  } = options;

  const [events, setEvents] = useState<AnalysisEvent[]>([]);
  const [progress, setProgress] = useState(0);
  const [isConnected, setIsConnected] = useState(false);
  const [isReconnecting, setIsReconnecting] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false); // Track connection attempt
  const [analysisError, setAnalysisError] = useState<string | null>(null); // Analysis error message
  const [canRetry, setCanRetry] = useState(false); // Whether user can retry
  const [isRetrying, setIsRetrying] = useState(false); // Backend is retrying
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const initialConnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const hasConnectedRef = useRef(false); // Track if we've ever successfully connected

  const connect = useCallback(() => {
    if (!sessionId) {
      console.warn("Cannot connect WebSocket: sessionId is null");
      return;
    }

    // Close existing connection if any
    if (wsRef.current) {
      if (wsRef.current.readyState === WebSocket.OPEN) {
        console.log("WebSocket already connected, skipping new connection");
        return;
      }
      wsRef.current.close();
      wsRef.current = null;
    }

    try {
      // Backend WebSocket endpoint: /api/v1/analysis/{session_id}/ws
      const wsUrl = `${WS_BASE_URL}/api/v1/analysis/${sessionId}/ws`;
      console.log("Connecting to WebSocket:", wsUrl);
      
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log("✅ WebSocket CONNECTED for session:", sessionId, "URL:", wsUrl);
        setIsConnected(true);
        setIsConnecting(false);
        setIsReconnecting(false);
        reconnectAttemptsRef.current = 0;
        hasConnectedRef.current = true; // Mark that we've successfully connected
        
        // Send initial ping to keep connection alive
        try {
          ws.send(JSON.stringify({ type: "ping" }));
          console.log("Sent initial ping to WebSocket");
        } catch (error) {
          console.warn("Failed to send initial ping:", error);
        }
      };

      ws.onmessage = (event) => {
        try {
          const data: AnalysisEvent = JSON.parse(event.data);
          
          // Handle pong/keepalive messages
          if (data.type === "pong" || (data as any).event === "keepalive") {
            return;
          }
          
          const eventWithTimestamp = {
            ...data,
            timestamp: data.timestamp || Date.now(),
          };

          console.log("📨 WebSocket event received:", {
            type: data.type,
            agent: data.agent,
            progress: data.progress,
            message: data.message,
            data: data.data,
            sessionId,
            timestamp: data.timestamp,
            rawDataLength: event.data.length,
            rawDataPreview: event.data.substring(0, 200), // Log first 200 chars for debugging
          });

          // Add event to array - React will batch updates, but we process all events in useEffect
          setEvents((prev) => {
            const updated = [...prev, eventWithTimestamp];
            console.log(`Events array updated: ${prev.length} -> ${updated.length} events`);
            return updated;
          });
          
          // Handle different event types
          if (data.type === "error" || data.type === "analysis_failed") {
            // Analysis failed - show error to user
            console.error("Analysis failed:", data.message, data.error);
            setAnalysisError(data.message || "Analysis failed. Please try again.");
            setCanRetry(data.can_retry || data.is_transient || false);
            setIsRetrying(false);
            setProgress(0); // Reset progress on failure
            onAnalysisFailed?.(data.message || "Analysis failed", data.can_retry || false);
          } else if (data.type === "warning") {
            // Transient error - backend is retrying
            console.warn("Analysis warning (retrying):", data.message);
            setIsRetrying(true);
            setAnalysisError(data.message || "Temporary issue, retrying...");
            // Don't reset progress - backend is still trying
          } else if (data.type === "retry") {
            // Backend is retrying
            console.log("Analysis retry:", data.message, `Attempt ${data.retry_attempt}/${data.max_retries}`);
            setIsRetrying(true);
            setAnalysisError(null); // Clear error since we're retrying
          } else if (data.type === "completed" || (data.type === "progress_update" && data.progress >= 100)) {
            // Handle completion - ensure progress is set to 100
            console.log("Analysis completed via WebSocket");
            setProgress(100); // Explicitly set to 100% on completion
            setAnalysisError(null); // Clear any errors
            setIsRetrying(false);
            setCanRetry(false);
            // Call completion callback but keep connection open
            onComplete?.();
          } else if (data.type === "progress_update") {
            // Only update overall progress from progress_update events
            // Agent events (agent_progress, agent_completed) have agent-specific progress
            setProgress(data.progress || 0);
            // Clear error state if we're making progress
            if (data.progress > 0) {
              setAnalysisError(null);
              setIsRetrying(false);
            }
          }
        } catch (error) {
          console.error("Failed to parse WebSocket message:", error, event.data);
        }
      };

      ws.onerror = (error) => {
        // WebSocket error event doesn't provide much info, check readyState
        const state = ws.readyState;
        
        // Only log errors if we've previously connected (to avoid noise from immediate closures)
        if (hasConnectedRef.current) {
          const errorMessage = state === WebSocket.CLOSED 
            ? "WebSocket connection closed unexpectedly"
            : state === WebSocket.CONNECTING
            ? "WebSocket connection failed"
            : "WebSocket error occurred";
          
          console.error("WebSocket error:", errorMessage, {
            readyState: state,
            url: wsUrl,
            sessionId,
          });
        } else {
          // Just log a warning for initial connection attempts
          console.debug("WebSocket connection attempt:", {
            readyState: state,
            url: wsUrl,
            sessionId,
          });
        }
        
        setIsConnected(false);
        // Don't call onError here - let onclose handle it with proper error codes
      };

      ws.onclose = (event) => {
        setIsConnected(false);
        setIsConnecting(false);
        
        // If we never successfully connected and it closed immediately, it might be a session issue
        const closedImmediately = !hasConnectedRef.current && event.code === 1006;
        
        console.log("WebSocket disconnected:", {
          code: event.code,
          reason: event.reason || "No reason provided",
          wasClean: event.wasClean,
          sessionId,
          closedImmediately,
        });

        // Don't reconnect if it was a normal closure due to component unmounting
        if (event.code === 1000 && event.reason === "Component unmounting") {
          console.log("WebSocket closed due to component unmounting - not reconnecting");
          return;
        }

        // Provide more specific error messages based on close codes
        if (event.code === 1006) {
          // Abnormal closure - connection lost
          if (closedImmediately) {
            console.warn("WebSocket closed immediately - session may not exist yet");
            // Don't treat immediate closures as errors if we haven't connected yet
            // This might be because the session doesn't exist
            if (waitForSession && reconnectAttemptsRef.current < maxReconnectAttempts) {
              reconnectAttemptsRef.current += 1;
              setIsReconnecting(true);
              
              reconnectTimeoutRef.current = setTimeout(() => {
                console.log(
                  `Retrying connection... (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})`
                );
                connect();
              }, reconnectDelay);
              return;
            }
          } else {
            console.warn("WebSocket connection lost (abnormal closure)");
          }
        } else if (event.code === 1001) {
          // Going away - server closed connection
          console.warn("WebSocket server closed connection");
        } else if (event.code === 1002) {
          // Protocol error
          onError?.(new Error("WebSocket protocol error"));
          return;
        } else if (event.code === 1003) {
          // Unsupported data
          onError?.(new Error("WebSocket unsupported data type"));
          return;
        } else if (event.code === 1008) {
          // Policy violation
          onError?.(new Error("WebSocket policy violation"));
          return;
        } else if (event.code === 1011) {
          // Server error
          onError?.(new Error("WebSocket server error"));
          return;
        }

        // Attempt reconnection if not a normal closure and auto-reconnect is enabled
        if (
          autoReconnect &&
          event.code !== 1000 && // Not a normal closure
          reconnectAttemptsRef.current < maxReconnectAttempts
        ) {
          reconnectAttemptsRef.current += 1;
          setIsReconnecting(true);

          reconnectTimeoutRef.current = setTimeout(() => {
            console.log(
              `Reconnecting... (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})`
            );
            connect();
          }, reconnectDelay);
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          onError?.(new Error(`Max reconnection attempts (${maxReconnectAttempts}) reached`));
        } else if (event.code === 1000) {
          // Normal closure - analysis might be complete
          console.log("WebSocket closed normally");
        }
      };
    } catch (error) {
      console.error("Failed to create WebSocket:", error);
      const errorMessage = error instanceof Error ? error.message : "Unknown error";
      onError?.(new Error(`Failed to create WebSocket: ${errorMessage}`));
    }
  }, [sessionId, autoReconnect, reconnectDelay, maxReconnectAttempts, onComplete, onError]);

  useEffect(() => {
    if (!sessionId) {
      return;
    }

    // Reset connection state when sessionId changes
    hasConnectedRef.current = false;
    reconnectAttemptsRef.current = 0;
    let isMounted = true;

    // Connect immediately - don't wait for session verification
    // The backend will handle missing sessions gracefully
    setIsConnecting(true);
    
    // Connect WebSocket IMMEDIATELY - don't wait for HTTP status check
    // This ensures we're connected before backend starts processing
    if (isMounted) {
      console.log(`🚀 Connecting WebSocket IMMEDIATELY for session: ${sessionId}`);
      // Use setTimeout with 0ms to ensure it runs after current execution context
      initialConnectTimeoutRef.current = setTimeout(() => {
        if (isMounted) {
          connect();
        }
      }, initialDelay);
    }
    
    // Fetch initial status in parallel (non-blocking)
    const fetchInitialStatus = async () => {
      try {
        const status = await apiClient.getAnalysisStatus(sessionId);
        if (status.progress !== undefined) {
          setProgress(status.progress);
        }
        console.log("Fetched initial status via HTTP:", status);
      } catch (error: any) {
        // Ignore errors - WebSocket will provide updates
        console.log("Initial status fetch failed (will use WebSocket):", error?.statusCode);
      }
    };
    
    // Fetch status in parallel, don't block WebSocket connection
    fetchInitialStatus();

    return () => {
      isMounted = false;
      if (initialConnectTimeoutRef.current) {
        clearTimeout(initialConnectTimeoutRef.current);
        initialConnectTimeoutRef.current = null;
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
      if (wsRef.current) {
        wsRef.current.close(1000, "Component unmounting");
        wsRef.current = null;
      }
    };
  }, [sessionId, waitForSession, initialDelay]); // Removed 'connect' from dependencies

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn("WebSocket is not connected. Cannot send message.");
    }
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close(1000, "Manual disconnect");
      wsRef.current = null;
    }
    setIsConnected(false);
    setIsReconnecting(false);
  }, []);

  // Function to clear error and allow retry
  const clearError = useCallback(() => {
    setAnalysisError(null);
    setCanRetry(false);
    setIsRetrying(false);
  }, []);

  return {
    events,
    progress,
    isConnected,
    isConnecting,
    isReconnecting,
    analysisError,
    canRetry,
    isRetrying,
    sendMessage,
    disconnect,
    clearError,
  };
}

