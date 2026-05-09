# 🔧 PLAN NAPRAW BACKEND - EXECUTION LOG

**Data Start**: 29.04.2026  
**Status**: ACTIVE EXECUTION  
**Owner**: Copilot

---

## 🎯 PRIORYTET 1 - KRYTYCZNE (TODAY)

### ✅ Task 1.1: Implementacja Zoom API
- **File**: `services/zoom.py`
- **Status**: IN PROGRESS
- **Changes**:
  - Dodaj real Zoom API integration
  - Fallback do mock URL
  - Environment variables: ZOOM_ACCOUNT_ID, ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET
- **Impact**: High - Rezerwacje mają rzeczywiste linki Zoom

### ✅ Task 1.2: PayPal Payment Capture Handler
- **File**: `services/payment_service.py`
- **Status**: IN PROGRESS
- **Changes**:
  - Implementacja `handle_successful_payment(order_id, resource)`
  - Update Reservation.payment_status = 'paid'
  - Generate Invoice
  - Send confirmation email
- **Impact**: Critical - Płatności muszą być finalizowane

### ✅ Task 1.3: Invoice PDF Generation Stub
- **File**: `services/invoice_service.py`
- **Status**: IN PROGRESS
- **Changes**:
  - Dodaj `generate_pdf()` function
  - Save PDF to disk/S3
  - Update Invoice.pdf_url
- **Impact**: High - Faktury muszą być dostępne

---

## 🎯 PRIORYTET 2 - WAŻNE (THIS WEEK)

### ✅ Task 2.1: Reset Password Implementation
- **File**: `routes/auth.py`
- **Status**: IN PROGRESS
- **Changes**:
  - Generowanie reset tokena
  - Wysłanie emaila z linkiem
  - Endpoint do zmiany hasła ze tokena
- **Impact**: Medium - Użytkownicy mogą zresetować hasło

### ✅ Task 2.2: Global Error Handler
- **File**: `app.py`
- **Status**: IN PROGRESS
- **Changes**:
  - @app.errorhandler dla 400, 401, 403, 404, 500
  - Unified error response format
  - Logging do console
- **Impact**: Medium - Consistency w error messages

### ✅ Task 2.3: Input Validation Schema
- **File**: `utils/validators.py` (NEW)
- **Status**: IN PROGRESS
- **Changes**:
  - JSON schema validation
  - Request decorator
  - Error handling
- **Impact**: Medium - Bezpieczne API

---

## 🎯 PRIORYTET 3 - OPTYMALIZACJA (NEXT MONTH)

### Task 3.1: N+1 Query Optimization
- **File**: Multiple routes
- **Status**: PLANNED
- **Changes**: Eager loading relationships

### Task 3.2: Rate Limiter Redis
- **File**: `app.py`
- **Status**: PLANNED
- **Changes**: Switch from memory:// to Redis

### Task 3.3: Test Suite
- **File**: `tests/` (NEW)
- **Status**: PLANNED
- **Changes**: Unit + Integration tests

---

## EXECUTION LOG

[STARTED] Plan napraw
[IN_PROGRESS] Task 1.1 - Zoom API
[IN_PROGRESS] Task 1.2 - Payment Capture
[IN_PROGRESS] Task 1.3 - PDF Invoice
[PENDING] Task 2.1 - Reset Password
[PENDING] Task 2.2 - Error Handler
[PENDING] Task 2.3 - Validators

