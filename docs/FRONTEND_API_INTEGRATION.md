# Frontend API Integration
The frontend communicates with the FastAPI backend strictly through centralized functions in `lib/api.ts`.

## Structure
- All endpoints are nested under `/api/v1/`.
- **Data Fetching:** Standard `fetch` with error handling and fallback dummy data where applicable for UI demonstration.
- **Type Safety:** Comprehensive TypeScript interfaces (`LiveQuote`, `FundamentalsData`, `MLPrediction`, `BacktestResponse`) map exactly to backend Pydantic DTOs.
- **CORS:** Controlled by backend `CORS_ORIGINS`.
