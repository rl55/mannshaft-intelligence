// frontend/hooks/use-websocket.ts
import { useEffect, useRef, useState } from 'react';

const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

interface AnalysisEvent {
  type: 'agent_started' | 'agent_completed' | 'guardrail_check' | 'evaluation_complete' | 'error';
  progress: number;
  agent?: string;
  data?: any;
}

export function useAnalysisWebSocket(sessionId: string | null) {
  const [events, setEvents] = useState<AnalysisEvent[]>([]);
  const [progress, setProgress] = useState(0);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!sessionId) return;

    const ws = new WebSocket(`${WS_BASE_URL}/ws/analysis/${sessionId}`);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      const data: AnalysisEvent = JSON.parse(event.data);
      setEvents((prev) => [...prev, data]);
      setProgress(data.progress);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
    };

    return () => {
      ws.close();
    };
  }, [sessionId]);

  return { events, progress, isConnected };
}