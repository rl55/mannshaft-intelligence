# Frontend-Backend Integration Guide

This document describes the complete integration between the frontend and backend, including API client, WebSocket connections, state management, error handling, and performance optimizations.

## Table of Contents

1. [API Client](#api-client)
2. [WebSocket Integration](#websocket-integration)
3. [State Management](#state-management)
4. [Error Handling](#error-handling)
5. [Caching](#caching)
6. [Performance Optimizations](#performance-optimizations)
7. [Environment Configuration](#environment-configuration)
8. [Deployment](#deployment)

## API Client

The API client (`lib/api.ts`) provides a robust interface to the backend API with:

- **Automatic retry logic** with exponential backoff
- **Response caching** with configurable TTL
- **Error handling** with user-friendly messages
- **Type-safe** request/response interfaces

### Usage

```typescript
import { apiClient } from "@/lib/api"

// Trigger analysis
const response = await apiClient.triggerAnalysis({
  week_number: 8,
  analysis_type: 'comprehensive',
  user_id: 'current_user'
})

// Get cached results (automatically cached)
const sessions = await apiClient.getSessions()

// Force refresh (skip cache)
const freshSessions = await apiClient.getSessions(true)
```

### Features

- **Retry Logic**: Automatically retries failed requests with exponential backoff
- **Caching**: GET requests are cached in localStorage with configurable TTL
- **Error Handling**: Converts API errors to user-friendly messages
- **Type Safety**: Full TypeScript support with typed interfaces

## WebSocket Integration

Real-time updates are handled through WebSocket connections using the `useAnalysisProgress` hook.

### Hook: `useAnalysisProgress`

Located in `hooks/use-analysis-progress.ts`, this hook provides:

- **Automatic reconnection** with configurable attempts
- **Event handling** for analysis progress updates
- **Connection status** tracking
- **Error recovery** mechanisms

### Usage

```typescript
import { useAnalysisProgress } from "@/hooks/use-analysis-progress"

function AnalysisComponent({ sessionId }: { sessionId: string }) {
  const { 
    events, 
    progress, 
    isConnected, 
    isReconnecting 
  } = useAnalysisProgress(sessionId, {
    autoReconnect: true,
    reconnectDelay: 3000,
    maxReconnectAttempts: 5,
    onComplete: () => {
      console.log("Analysis completed!")
    },
    onError: (error) => {
      console.error("WebSocket error:", error)
    }
  })

  return (
    <div>
      <div>Progress: {progress}%</div>
      <div>Status: {isConnected ? "Connected" : "Disconnected"}</div>
      {events.map((event, i) => (
        <div key={i}>{event.message}</div>
      ))}
    </div>
  )
}
```

### WebSocket Events

The backend sends events with the following structure:

```typescript
interface AnalysisEvent {
  type: 'agent_started' | 'agent_completed' | 'progress_update' | 'completed' | 'error'
  progress: number
  agent?: string
  data?: any
  message?: string
  timestamp?: number
}
```

## State Management

Global state is managed using Zustand (`store/analysis-store.ts`).

### Store: `useAnalysisStore`

Provides centralized state management for:

- Current analysis session and results
- Session list
- Cache statistics
- Monitoring data (agents, guardrails, Gemini usage)

### Usage

```typescript
import { useAnalysisStore } from "@/store/analysis-store"

function MyComponent() {
  const { 
    currentSession,
    triggerAnalysis,
    fetchSessions,
    clearCache 
  } = useAnalysisStore()

  const handleStart = async () => {
    await triggerAnalysis(8, 'comprehensive', 'user123')
  }

  return (
    <div>
      {currentSession && (
        <div>Session: {currentSession.session_id}</div>
      )}
    </div>
  )
}
```

### Persistence

The store automatically persists:
- Current session
- Current result

Data is stored in localStorage and restored on page reload.

## Error Handling

Comprehensive error handling is provided through `lib/error-handler.ts`.

### Features

- **Retry with exponential backoff**
- **User-friendly error messages**
- **Toast notifications**
- **Network error detection**

### Usage

```typescript
import { retryWithBackoff, handleAPIError, APIError } from "@/lib/error-handler"

try {
  const result = await retryWithBackoff(
    () => apiClient.getSessions(),
    {
      maxRetries: 3,
      initialDelay: 1000,
      backoffMultiplier: 2
    }
  )
} catch (error) {
  handleAPIError(error, "Failed to load sessions")
}
```

### Error Types

- **APIError**: Custom error class with status code and response data
- **Network Errors**: Automatically detected and handled
- **Retryable Errors**: Status codes 408, 429, 500, 502, 503, 504

## Caching

Response caching is handled by `lib/cache.ts` using localStorage.

### Features

- **Automatic expiration** based on TTL
- **Storage quota handling**
- **Cache invalidation**
- **Expired entry cleanup**

### Usage

```typescript
import { cacheManager } from "@/lib/cache"

// Set cache with 5 minute TTL
cacheManager.set('my-key', data, 5 * 60 * 1000)

// Get cached data
const cached = cacheManager.get('my-key')

// Clear all cache
cacheManager.clear()

// Clear expired entries
cacheManager.clearExpired()
```

### Cache Strategy

- **Analysis Status**: 5 seconds TTL (frequently changing)
- **Analysis Results**: 5 minutes TTL (stable data)
- **Sessions List**: 30 seconds TTL
- **Monitoring Data**: 30-60 seconds TTL

## Performance Optimizations

### Code Splitting

Components are lazy-loaded using React.lazy:

```typescript
import { AgentPerformanceChart } from "@/lib/lazy-load"

function Dashboard() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <AgentPerformanceChart />
    </Suspense>
  )
}
```

### Webpack Configuration

Optimized in `next.config.mjs`:

- **Vendor chunking** for large libraries
- **Common chunk** for shared code
- **Package optimization** for lucide-react and recharts

### Best Practices

1. **Lazy load charts** and heavy components
2. **Use Suspense** boundaries for loading states
3. **Cache API responses** to reduce network calls
4. **Virtualize lists** for large datasets (future enhancement)
5. **Service worker** for offline support (future enhancement)

## Environment Configuration

### Required Variables

Create `.env.local` (not committed to git):

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_ENV=development
```

### Production Variables

For production deployments (Vercel):

- `NEXT_PUBLIC_API_URL`: Production API URL
- `NEXT_PUBLIC_WS_URL`: Production WebSocket URL
- `NEXT_PUBLIC_ENV`: `production`

## Deployment

### Frontend (Vercel)

1. Connect GitHub repository to Vercel
2. Configure environment variables
3. Deploy automatically on push to `main`

### Backend (Docker)

1. Build Docker image:
   ```bash
   docker build -f docker/Dockerfile.backend -t mannshaft-backend .
   ```

2. Run with docker-compose:
   ```bash
   docker-compose up -d
   ```

### CI/CD

GitHub Actions workflows:

- **Frontend CI**: Lint, type check, build
- **Backend CI**: Tests, lint, Docker build
- **Auto-deploy**: Deploy to production on merge to `main`

## Example: Complete Integration Flow

```typescript
import { useAnalysisStore } from "@/store/analysis-store"
import { useAnalysisProgress } from "@/hooks/use-analysis-progress"
import { useToast } from "@/hooks/use-toast"

function AnalysisPage() {
  const { triggerAnalysis, currentSession } = useAnalysisStore()
  const { toast } = useToast()
  const [sessionId, setSessionId] = useState<string | null>(null)

  const { events, progress, isConnected } = useAnalysisProgress(sessionId, {
    onComplete: async () => {
      toast({
        title: "Analysis Complete",
        description: "Your analysis has been completed",
      })
    }
  })

  const handleStart = async () => {
    try {
      const response = await triggerAnalysis(8, 'comprehensive', 'user123')
      setSessionId(response.session_id)
    } catch (error) {
      // Error handled automatically
    }
  }

  return (
    <div>
      <button onClick={handleStart}>Start Analysis</button>
      {sessionId && (
        <div>
          <div>Progress: {progress}%</div>
          <div>Connected: {isConnected ? "Yes" : "No"}</div>
          {events.map((event, i) => (
            <div key={i}>{event.message}</div>
          ))}
        </div>
      )}
    </div>
  )
}
```

## Troubleshooting

### WebSocket Connection Issues

1. Check `NEXT_PUBLIC_WS_URL` environment variable
2. Verify backend WebSocket endpoint is running
3. Check browser console for connection errors
4. Ensure CORS is configured correctly

### API Errors

1. Verify `NEXT_PUBLIC_API_URL` is correct
2. Check network tab for failed requests
3. Review error messages in toast notifications
4. Check backend logs for server-side errors

### Cache Issues

1. Clear browser localStorage
2. Use `cacheManager.clear()` to reset cache
3. Check cache TTL settings
4. Verify cache keys are unique

## Future Enhancements

- [ ] Service worker for offline support
- [ ] Virtualized lists for large datasets
- [ ] Optimistic UI updates
- [ ] Request deduplication
- [ ] Background sync
- [ ] Push notifications for completed analyses

