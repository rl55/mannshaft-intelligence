# Quick Start Guide - Frontend-Backend Integration

## Setup

1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Configure environment variables**
   Create `.env.local`:
   ```bash
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_WS_URL=ws://localhost:8000
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

## Key Files

### API Client
- `lib/api.ts` - Enhanced API client with retry, caching, error handling
- `lib/error-handler.ts` - Error handling utilities
- `lib/cache.ts` - LocalStorage caching manager

### State Management
- `store/analysis-store.ts` - Zustand store for global state

### WebSocket
- `hooks/use-analysis-progress.ts` - Real-time analysis progress hook

### Components
- `components/quick-actions-card.tsx` - Updated to use store
- `components/analysis/enhanced-analysis-view.tsx` - Real-time analysis view

## Usage Examples

### Trigger Analysis
```typescript
import { useAnalysisStore } from "@/store/analysis-store"

const { triggerAnalysis } = useAnalysisStore()
const response = await triggerAnalysis(8, 'comprehensive', 'user123')
```

### Monitor Progress
```typescript
import { useAnalysisProgress } from "@/hooks/use-analysis-progress"

const { progress, events, isConnected } = useAnalysisProgress(sessionId)
```

### Fetch Data with Caching
```typescript
import { apiClient } from "@/lib/api"

// Cached (default)
const sessions = await apiClient.getSessions()

// Force refresh
const freshSessions = await apiClient.getSessions(true)
```

## Features

✅ **Retry Logic** - Automatic retry with exponential backoff  
✅ **Response Caching** - localStorage caching with TTL  
✅ **Error Handling** - User-friendly error messages  
✅ **WebSocket** - Real-time updates with auto-reconnect  
✅ **State Management** - Zustand store with persistence  
✅ **Performance** - Code splitting and lazy loading  
✅ **CI/CD** - GitHub Actions workflows  

## Next Steps

1. Review `INTEGRATION.md` for detailed documentation
2. Check `.github/workflows/` for CI/CD configuration
3. Update environment variables for production
4. Test WebSocket connection with backend

