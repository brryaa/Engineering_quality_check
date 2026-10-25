# Work Package 3: Fault Injection & Resilience Testing Report

## 1. Executive Summary
A dedicated fault injection framework was designed and executed against the Engineering Quality Lab (EQL) backend. The test suite simulates real-world edge conditions, network failures, unexpected crashes, malformed payloads, out-of-bounds pagination, and database interruptions.

## 2. Fault Scenarios & Verification Evidence

| Fault Scenario | Injected Condition | Expected Response | System Behavior & Mitigation | Result |
| :--- | :--- | :--- | :--- | :--- |
| **Malformed JSON** | Truncated syntax `{"code": ... }` | `HTTP 422 Unprocessable` | FastAPI body parser intercepts without unhandled exception | **PASS** |
| **Invalid Schema Types** | String supplied for integer FK / float | `HTTP 422 Unprocessable` | Pydantic V2 validation catches type mismatches | **PASS** |
| **Out-of-Bounds Pagination** | `page=1,000,000` with `limit=100` | `HTTP 200` with `items: []` | Repository offset/limit handles empty set without query crash | **PASS** |
| **Illegal Pagination Parameters**| `page=0`, `page=-5`, `page_size=10,000` | `HTTP 422 Unprocessable` | FastAPI `Query(ge=1, le=100)` validates parameters | **PASS** |
| **Duplicate Request Replay** | Identical unique codes submitted | `HTTP 409 Conflict` | Service layer detects collision before database error | **PASS** |
| **Resource 404 Resiliency** | ID 999999 queried across all 9 modules | `HTTP 404 Not Found` | Structured `{success: false, error: "..."}` response | **PASS** |
| **Database Connection Drop** | Simulated `OperationalError` on SQL connection | `HTTP 503 Service Unavailable` | Specialized handler returns sanitized message with reference ID | **PASS** |
| **Optimistic Lock Collision** | Concurrent update throwing `StaleDataError` | `HTTP 409 Conflict` | Handler alerts user that record was modified by another user | **PASS** |
| **Unhandled Runtime Crash** | Unhandled exception with mock secret string | `HTTP 500 Internal Error` | Error masked to prevent credential / internal traceback leaks | **PASS** |

## 3. Engineering Improvements Implemented
1. **Centralized Exception Handlers (`backend/app/core/exceptions.py`)**:
   - `stale_data_exception_handler`: maps SQLAlchemy `StaleDataError` to `HTTP 409 Conflict`.
   - `db_operational_exception_handler`: maps `OperationalError` to `HTTP 503 Service Unavailable`.
   - `db_integrity_exception_handler`: maps `IntegrityError` to `HTTP 400 Bad Request`.
   - `generic_exception_handler`: generates random 8-character `reference_id` and strips raw stack traces from production client responses.
2. **Automated Verification**:
   - `backend/tests/test_fault_injection.py`: 9/9 automated tests passing.
