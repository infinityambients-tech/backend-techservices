# 📊 AUDYT TECHNICZNY - BACKEND TechServices

**Data**: 29.04.2026  
**Wersja**: 1.0  
**Projekt**: TechServices - Platforma rezerwacji usług online

---

## 📑 Spis Treści
1. [Struktura Projektu](#struktura-projektu)
2. [Stack Technologiczny](#stack-technologiczny)
3. [Architektura Systemu](#architektura-systemu)
4. [Modele Danych](#modele-danych)
5. [API Routes & Endpoints](#api-routes--endpoints)
6. [Services & Serwisy](#services--serwisy)
7. [Funkcje Szczegółowe](#funkcje-szczegółowe)
8. [Zależności Między Funkcjami](#zależności-między-funkcjami)
9. [Configuration & Extensions](#configuration--extensions)
10. [Problemy & TODO](#problemy--todo)

---

## 🗂️ Struktura Projektu

```
backend/
├── app.py                          # Główny plik aplikacji Flask
├── models.py                       # ORM modele (SQLAlchemy)
├── extensions.py                   # Inicjalizacja extensionów
├── requirements.txt                # Zależności Python
│
├── routes/                         # API Routes (blueprints)
│   ├── __init__.py
│   ├── auth.py                    # Rejestracja, login, weryfikacja
│   ├── offers.py                  # Zarządzanie ofertami
│   ├── reservations.py            # Rezerwacje
│   ├── slots.py                   # Terminy dostępności
│   ├── user.py                    # Profile użytkowników
│   ├── contact.py                 # Formularz kontaktowy
│   └── payment.py                 # Płatności (PayPal)
│
├── services/                       # Serwisy biznesowe
│   ├── reservation_service.py     # Logika rezerwacji (atomic lock)
│   ├── payment_service.py         # Integracja PayPal
│   ├── email.py                   # Wysyłanie emaili (SMTP)
│   ├── zoom.py                    # Generowanie linków Zoom (TODO)
│   ├── discord.py                 # Powiadomienia Discord
│   ├── analysis_service.py        # Analiza danych & AI rekomendacje
│   ├── recommender_service.py     # Rekomendacje produktów
│   ├── invoice_service.py         # Generowanie faktur
│   └── webhook_service.py         # Webhook'i PayPal
│
├── migrations/                     # Alembic migracje bazy danych
│   ├── versions/
│   └── env.py
│
├── deployment/                     # Konfiguracja serwerów
│   ├── techservices.nginx         # Nginx config
│   └── techservices.service       # Systemd service file
│
├── instance/                       # Pliki instancji (baza danych)
│   └── app.db                     # SQLite (development)
│
└── [Utility Scripts]
    ├── add_reserved_until.py
    ├── check_db.py
    ├── fix_schema.py
    ├── migrate_*.py
    └── test_delete.py
```

---

## 🔧 Stack Technologiczny

### Framework & Core
| Biblioteka | Wersja | Zastosowanie |
|-----------|--------|-------------|
| Flask | Latest | Micro-framework webowy |
| Flask-SQLAlchemy | Latest | ORM do bazy danych |
| Flask-Migrate | Latest | Migracje bazy danych (Alembic) |
| Flask-CORS | Latest | Cross-Origin Resource Sharing |
| Flask-JWT-Extended | Latest | Token JWT dla autentykacji |
| Flask-Mail | Latest | Wysyłanie emaili (SMTP) |
| Flask-Limiter | Latest | Rate limiting (throttling) |

### Baza Danych
| Komponenta | Opis |
|-----------|------|
| SQLAlchemy | ORM mapowanie relacyjne |
| SQLite | Development (sqlite:///instance/app.db) |
| PostgreSQL | Production (psycopg2-binary) |

### Integracjeby Zewnętrzne
| Serwis | Zastosowanie |
|--------|-------------|
| PayPal API | Przetwarzanie płatności |
| Zoom API | Generowanie linków do spotkań (TODO) |
| Discord Webhooks | Powiadomienia czasu rzeczywistego |
| Gmail/SMTP | Wysyłanie emaili |

### Utilities
| Biblioteka | Zastosowanie |
|-----------|-------------|
| python-dotenv | Zmienne środowiskowe (.env) |
| requests | HTTP requesty |
| Celery + Redis | Async tasks (opcjonalnie) |
| Werkzeug | Security utilities |
| Gunicorn | WSGI server (production) |

---

## 🏗️ Architektura Systemu

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React/Vite)                     │
│              (admin/ + frontend-techservices/)              │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    NGINX REVERSE PROXY                       │
│                   (deployment/nginx)                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
    ┌──────────────┐        ┌──────────────┐
    │ Gunicorn     │        │ Gunicorn     │
    │ (port 5000)  │        │ (port 5001)  │
    └──────┬───────┘        └──────┬───────┘
           │                       │
           └───────────┬───────────┘
                       ▼
    ┌──────────────────────────────────────┐
    │      Flask Application (app.py)      │
    ├──────────────────────────────────────┤
    │  • Blueprint Routes (/api/*)         │
    │  • JWT Authentication                │
    │  • Rate Limiting                     │
    │  • CORS Headers                      │
    └──────────────────────────────────────┘
           │
    ┌──────┼──────────────────┐
    │      │                  │
    ▼      ▼                  ▼
  Routes Services          Extensions
   • auth    • reservation    • db (SQLAlchemy)
   • offers  • payment        • jwt (JWT Manager)
   • slots   • email          • mail (Flask-Mail)
   • user    • zoom           • limiter (Rate)
   • contact • discord        • cors (CORS)
   • payment • analysis
            • recommender
            • invoice
            • webhook
    │
    └──────────────────┬─────────────────┐
                       │                 │
                ▼              ▼         ▼
            SQLite        PostgreSQL   Redis
           (dev)         (production) (cache/queue)
            │
        instance/app.db
```

---

## 🗄️ Modele Danych (Entity-Relationship Diagram)

### Tabele i Relacje

```
┌──────────────────┐        ┌──────────────────┐
│     USERS        │        │    TENANTS       │
├──────────────────┤        ├──────────────────┤
│ id (PK)          │        │ id (PK)          │
│ tenant_id (FK) ──┼────────→ id               │
│ email            │        │ name             │
│ password_hash    │        │ domain           │
│ first_name       │        │ company_name     │
│ last_name        │        │ company_nip      │
│ phone            │        │ company_address  │
│ role             │        │ created_at       │
│ is_verified      │        └──────────────────┘
│ verification_token
│ failed_attempts  │
│ created_at       │
└──────────────────┘
    │
    │ 1:M
    ├─────────────┬──────────────┐
    │             │              │
    ▼             ▼              ▼
┌─────────────┐ ┌──────────────────┐ ┌──────────────┐
│RESERVATIONS │ │ SUBSCRIPTIONS    │ │CONNECTED_ACT │
├─────────────┤ ├──────────────────┤ ├──────────────┤
│ id (PK)     │ │ id (PK)          │ │ id (PK)      │
│ user_id (FK)│ │ user_id (FK)     │ │ user_id (FK) │
│ offer_id(FK)│ │ paypal_sub_id    │ │ paypal_email │
│ time_slot_id│ │ status           │ │ merchant_id  │
│ meeting_link│ │ current_period_end
│ notes       │ │ created_at       │ │ is_active    │
│ manual_dt   │ └──────────────────┘ │ created_at   │
│ status      │                      └──────────────┘
│ payment_st  │
│ created_at  │
└─────────────┘
    │
    ├─────────────┬────────────┐
    │             │            │
    ▼             ▼            ▼
┌──────────────┐ ┌──────────┐ ┌─────────────┐
│ OFFERS       │ │TIMESLOTS │ │ PAYMENTS    │
├──────────────┤ ├──────────┤ ├─────────────┤
│ id (PK)      │ │ id (PK)  │ │ id (PK)     │
│ name         │ │ start_tm │ │ reserv_id(FK)
│ description  │ │ end_tm   │ │ paypal_ord_id
│ price_from   │ │ is_avail │ │ paypal_pay_id
│ price_to     │ │ reserved_by(FK) │ amount  │
│ duration_days│ │ reserved_until  │ currency│
│ is_active    │ │ created_at  │ │ status  │
│ is_featured  │ │          │ │ created_at  │
│ is_generated │ └──────────┘ └─────────────┘
│ source_offers│        ▲
│ created_at   │        │
└──────────────┘        │
    │                   │
    └───────────────────┘
            1:M

┌───────────────────┐    ┌──────────────────┐
│ OFFER_STATISTICS  │    │ CONTACT_MESSAGES │
├───────────────────┤    ├──────────────────┤
│ id (PK)           │    │ id (PK)          │
│ offer_id (FK)     │    │ name             │
│ views             │    │ email            │
│ reservations_cnt  │    │ message          │
│ conversions       │    │ status           │
│ last_reserved_at  │    │ created_at       │
│ updated_at        │    └──────────────────┘
└───────────────────┘

┌──────────────────┐     ┌──────────────────┐
│ INVOICES         │     │ INVOICE_SEQUENCE │
├──────────────────┤     ├──────────────────┤
│ id (PK)          │     │ id (PK)          │
│ user_id (FK)     │     │ year             │
│ reserv_id (FK)   │     │ month            │
│ payment_id (FK)  │     │ last_value       │
│ invoice_number   │     └──────────────────┘
│ net_amount       │
│ vat_rate         │
│ vat_amount       │
│ gross_amount     │
│ buyer_name       │
│ buyer_address    │
│ buyer_nip        │
│ pdf_url          │
│ issued_at        │
│ created_at       │
└──────────────────┘

┌──────────────────┐     ┌──────────────────┐
│SUBSCRIPTION_PLANS│     │ COUPONS          │
├──────────────────┤     ├──────────────────┤
│ id (PK)          │     │ id (PK)          │
│ name             │     │ code             │
│ description      │     │ discount_type    │
│ paypal_plan_id   │     │ value            │
│ price            │     │ max_uses         │
│ interval         │     │ used_count       │
│ is_active        │     │ valid_until      │
└──────────────────┘     │ is_active        │
                         │ created_at       │
                         └──────────────────┘
```

### Klucze i Relacje

```
Users
  ├── 1:M → Reservations
  ├── 1:M → Subscriptions
  ├── 1:M → ConnectedAccounts
  ├── M:1 → Tenants

Offers
  ├── 1:1 → OfferStatistics
  ├── 1:M → Reservations
  ├── 1:M → TimeSlots (virtual)

TimeSlots
  ├── 1:M → Reservations
  └── M:1 → Users (reserved_by)

Reservations
  ├── M:1 → Users
  ├── M:1 → Offers
  ├── M:1 → TimeSlots
  └── 1:M → Payments

Payments
  ├── M:1 → Reservations
  └── 1:1 → Invoices

Tenants
  ├── 1:M → Users
  ├── 1:M → Offers
  ├── 1:M → Invoices
  └── 1:M → Reservations
```

---

## 🔌 API Routes & Endpoints

### 1. **AUTH ROUTES** (`/api/auth`)

#### `POST /register`
```python
def register():
    """
    Rejestracja nowego użytkownika.
    
    Request (JSON):
    {
        "email": "user@example.com",
        "password": "password123",  # min. 8 znaków
        "first_name": "Jan",
        "last_name": "Kowalski",
        "phone": "+48123456789"
    }
    
    Response (201):
    {
        "message": "Zarejestrowano pomyślnie. Możesz się teraz zalogować."
    }
    
    Errors:
    - 400: Nieprawidłowy email / hasło za krótkie / email istnieje
    - 500: Błąd bazy danych
    
    Rate Limit: 10 per minute
    Dependencies:
    - valid_email() - walidacja formatu email
    - valid_password() - walidacja hasła (min 8 znaków)
    - User.set_password() - hashing hasła
    
    Notes:
    ✅ Użytkownik jest automatycznie zweryfikowany (is_verified=True)
    ✅ Brak wysyłania emaila weryfikacyjnego
    """
```

#### `POST /login`
```python
def login():
    """
    Logowanie użytkownika.
    
    Request (JSON):
    {
        "email": "user@example.com",
        "password": "password123"
    }
    
    Response (200):
    {
        "message": "Zalogowano",
        "access_token": "eyJ0eXAiOiJKV1QiLC...",
        "role": "user"  # lub "admin"
    }
    
    Errors:
    - 401: Błędne dane logowania
    
    Rate Limit: 10 per minute
    Dependencies:
    - User.check_password() - weryfikacja hasła
    - create_access_token() - generowanie JWT
    
    Notes:
    ✅ Sprawdzenie is_verified zostało usunięte
    ✅ Resetowanie failed_attempts counter
    """
```

#### `GET /verify/<token>`
```python
def verify_email(token):
    """
    Weryfikacja email'a (legacy endpoint, teraz nieużywany).
    
    Response (200):
    HTML z potwierdzeniem aktywacji konta
    
    Errors:
    - 400: Link nieprawidłowy lub wygasł
    - 500: Błąd serwera
    """
```

#### `GET /me` (Protected)
```python
@jwt_required()
def me():
    """
    Pobranie danych zalogowanego użytkownika.
    
    Headers:
    Authorization: Bearer <token>
    
    Response (200):
    {
        "id": "uuid",
        "email": "user@example.com",
        "first_name": "Jan",
        "last_name": "Kowalski",
        "phone": "+48123456789",
        "role": "user",
        "is_verified": true,
        "created_at": "2026-04-29T10:00:00"
    }
    
    Errors:
    - 401: Brak/nieprawidłowy token
    - 404: Użytkownik nie znaleziony
    """
```

#### `POST /logout` (Protected)
```python
@jwt_required()
def logout():
    """
    Wylogowanie użytkownika (stateless - token traci ważność).
    
    Response (200):
    {"message": "Wylogowano"}
    """
```

#### `POST /reset-password`
```python
def reset_password():
    """
    Reset hasła (placeholder - email system later).
    
    Request (JSON):
    {"email": "user@example.com"}
    
    Response (200):
    {"message": "Jeśli konto istnieje, wysłano link"}
    
    Rate Limit: 5 per minute
    
    TODO: Implementacja wysyłki emaila resetującego
    """
```

---

### 2. **OFFERS ROUTES** (`/api/offers`)

#### `GET /`
```python
def get_offers():
    """
    Pobranie wszystkich aktywnych ofert.
    
    Query Params:
    (brak)
    
    Response (200):
    [{
        "id": "uuid",
        "name": "Konsultacja IT",
        "description": "Profesjonalna konsultacja",
        "price_from": 500,
        "price_to": 2000,
        "duration_label": "2-4 tygodnie",
        "is_active": true,
        "is_featured": false,
        "is_generated": false,
        "source_offers": [],
        "created_at": "2026-04-29T10:00:00",
        "stats": {
            "views": 42,
            "conversions": 5,
            "reservations_count": 3
        }
    }]
    """
```

#### `GET /<offer_id>`
```python
def get_offer(offer_id):
    """
    Pobranie szczegółów konkretnej oferty (z aktualizacją statystyk).
    
    Response (200):
    {...} - jak wyżej
    
    Dependencies:
    - offer.update_stats('view') - inkrementacja liczby views
    
    Errors:
    - 404: Oferta nie znaleziona
    """
```

#### `POST /generate-optimal` (Admin)
```python
@jwt_required()
def generate_optimal_offer():
    """
    Generowanie optymalnej oferty bundle'a (tylko admin).
    
    Response (201):
    {...} - nowa wygenerowana oferta
    
    Dependencies:
    - AnalysisService.identify_optimal_offer()
    
    Errors:
    - 403: Brak uprawnień admin
    - 400: Zbyt mało ofert do stworzenia bundle'a
    """
```

#### `GET /insights`
```python
def get_insights():
    """
    Pobranie trendów rynkowych.
    
    Response (200):
    {"insights": "Najchętniej wybierany pakiet to 'Konsultacja IT' (12 zakupów)."}
    
    Dependencies:
    - AnalysisService.get_market_insights()
    """
```

#### `GET /recommendations` (Protected)
```python
@jwt_required()
def get_recommendations():
    """
    Pobranie personalizowanych rekomendacji dla użytkownika.
    
    Response (200):
    [{...}] - lista oferowanych ofert
    
    Dependencies:
    - RecommendationService.get_recommendations_for_user(user_id)
    """
```

#### `POST /` (Admin Create)
```python
def create_offer():
    """
    Tworzenie nowej oferty.
    
    Request (JSON):
    {
        "name": "Konsultacja IT",
        "description": "...",
        "price_from": 500,
        "price_to": 2000,
        "duration_days": 30,
        "duration_label": "2-4 tygodnie",
        "is_active": true,
        "is_featured": false
    }
    
    Response (201):
    {...} - utworzona oferta
    """
```

#### `PUT /<offer_id>` (Admin Update)
```python
def update_offer(offer_id):
    """
    Aktualizacja oferty.
    """
```

#### `PATCH /<offer_id>/toggle` (Admin)
```python
def toggle_offer(offer_id):
    """
    Włączenie/wyłączenie oferty.
    
    Response (200):
    {"is_active": true/false}
    """
```

#### `DELETE /<offer_id>` (Admin)
```python
def delete_offer(offer_id):
    """
    Usunięcie oferty.
    """
```

---

### 3. **RESERVATIONS ROUTES** (`/api/reservations`)

#### `POST /` (Protected)
```python
@jwt_required()
def create_reservation():
    """
    Tworzenie nowej rezerwacji.
    
    Request (JSON):
    {
        "offer_id": "uuid",
        "time_slot_id": "uuid",  # opcjonalnie
        "manual_datetime": "2026-05-15T14:00:00",  # alternatywa
        "notes": "Dodatkowe uwagi"
    }
    
    Response (201):
    {
        "message": "Rezerwacja utworzona",
        "reservation_id": "uuid",
        "meeting_link": "https://zoom.us/j/..."
    }
    
    Errors:
    - 400: Brak time_slot_id lub manual_datetime
    - 404: Oferta nie znaleziona
    - 409: Termin niedostępny (SlotUnavailableError)
    
    Dependencies:
    - create_reservation_atomic() - atomic lock na slocie
    - generate_zoom_link() - generowanie linku Zoom
    - send_email() - powiadomienie emailem
    - send_discord_notification() - alert w Discord
    
    Side Effects:
    ✅ Aktualizacja OfferStatistics.reservations_count
    ✅ Wysłanie emaila do użytkownika
    ✅ Powiadomienie w Discord
    """
```

#### `GET /`
```python
def get_all_reservations():
    """
    Pobranie wszystkich rezerwacji (admin).
    
    Response (200):
    [{
        "id": "uuid",
        "user_id": "uuid",
        "offer_id": "uuid",
        "time_slot_id": "uuid",
        "meeting_link": "https://zoom.us/...",
        "notes": "",
        "status": "new",
        "payment_status": "unpaid",
        "manual_datetime": null,
        "created_at": "2026-04-29T10:00:00",
        "offer_name": "Konsultacja IT",
        "start_time": "2026-05-15T14:00:00",
        "user_email": "user@example.com"
    }]
    """
```

#### `GET /user/<user_id>`
```python
def get_user_reservations(user_id):
    """
    Pobranie rezerwacji konkretnego użytkownika.
    """
```

#### `PATCH /<reservation_id>/status`
```python
def update_status(reservation_id):
    """
    Aktualizacja statusu rezerwacji.
    
    Request (JSON):
    {"status": "confirmed"}  # new, confirmed, done, cancelled
    
    Response (200):
    {...} - rezerwacja
    """
```

#### `PATCH /<reservation_id>/cancel`
```python
def cancel_reservation(reservation_id):
    """
    (Snippet nie przeczytany całkowicie)
    Anulowanie rezerwacji.
    """
```

---

### 4. **TIME SLOTS ROUTES** (`/api/slots`)

#### `GET /`
```python
def get_slots():
    """
    Pobranie dostępnych terminów.
    
    Query Params:
    ?week=2026-04-29  # filtrowanie po tygodniu (YYYY-MM-DD)
    
    Response (200):
    [{
        "id": "uuid",
        "start": "2026-05-15T14:00:00",
        "end": "2026-05-15T15:00:00",
        "is_available": true
    }]
    
    Logic:
    - Zwraca tylko sloty gdzie is_available=True
    - Pomija sloty z reserved_until w przyszłości (15min lock)
    """
```

#### `POST /`
```python
def create_slot():
    """
    Tworzenie nowego terminu.
    
    Request (JSON):
    {
        "start_time": "2026-05-15T14:00:00",
        "end_time": "2026-05-15T15:00:00"
    }
    
    Response (201):
    {...}
    """
```

#### `DELETE /<slot_id>`
```python
def delete_slot(slot_id):
    """
    Usunięcie terminu.
    """
```

#### `POST /bulk`
```python
def bulk_create_slots():
    """
    Zbiorowe tworzenie terminów (admin calendar).
    
    Request (JSON):
    {
        "slots": [
            {"start_time": "...", "end_time": "..."},
            ...
        ]
    }
    
    Response (201):
    [{...}] - lista utworzonych slotów
    """
```

---

### 5. **USER ROUTES** (`/api/user`)

#### `GET /profile` (Protected)
```python
@jwt_required()
def get_profile():
    """
    Pobranie profilu zalogowanego użytkownika.
    """
```

#### `PUT /profile` (Protected)
```python
@jwt_required()
def update_profile():
    """
    Aktualizacja profilu.
    
    Request (JSON):
    {
        "first_name": "Jan",
        "last_name": "Kowalski",
        "phone": "+48123456789",
        "password": "newpassword123"  # opcjonalnie
    }
    """
```

#### `GET /reservations` (Protected)
```python
@jwt_required()
def get_my_reservations():
    """
    Pobranie moich rezerwacji.
    """
```

#### `GET /all` (Admin Only)
```python
@jwt_required()
def get_all_users():
    """
    Pobranie listy wszystkich użytkowników.
    
    Errors:
    - 403: Brak uprawnień admin
    """
```

---

### 6. **CONTACT ROUTES** (`/api/contact`)

#### `POST /`
```python
def send_message():
    """
    Wysłanie wiadomości kontaktowej.
    
    Request (JSON):
    {
        "name": "Jan Kowalski",
        "email": "user@example.com",
        "message": "Mam pytanie..."
    }
    
    Response (201):
    {"message": "Wiadomosc wyslana"}
    
    Errors:
    - 400: Brakujące pola
    
    Dependencies:
    - send_email() - wysłanie do odbiorcy
    
    Side Effects:
    ✅ Zapisanie wiadomości w bazie
    ✅ Wysłanie emaila do CONTACT_RECEIVER_EMAIL
    """
```

#### `GET /`
```python
def get_messages():
    """
    Pobranie wszystkich wiadomości kontaktowych.
    """
```

#### `PATCH /<msg_id>/status`
```python
def update_status(msg_id):
    """
    Zmiana statusu wiadomości.
    
    Request (JSON):
    {"status": "read"}  # new, read, archived
    """
```

---

### 7. **PAYMENT ROUTES** (`/api/payments`)

#### `POST /create-order`
```python
def create():
    """
    Tworzenie zamówienia PayPal.
    
    Request (JSON):
    {"amount": 5000}  # PLN (w centach)
    
    Response (200):
    {"approval_url": "https://www.paypal.com/checkoutnow?token=..."}
    
    Dependencies:
    - payment_service.create_order()
    
    Errors:
    - 400: Brak kwoty
    - 500: Błąd PayPal API
    """
```

#### `GET /invoices`
```python
def get_invoices():
    """
    Pobranie listy faktur (placeholder).
    
    Response (200):
    []  # Na razie pusta lista
    
    TODO: Implementacja pobierania faktur z bazy
    """
```

---

## 🔧 Services & Serwisy

### 1. **reservation_service.py**

#### `create_reservation_atomic()`
```python
def create_reservation_atomic(user_id, offer_id, time_slot_id, manual_datetime=None, notes=''):
    """
    Atomowe zablokowanie terminu i utworzenie rezerwacji.
    
    Parameters:
    - user_id: str (UUID użytkownika)
    - offer_id: str (UUID oferty)
    - time_slot_id: str | None (UUID terminu)
    - manual_datetime: datetime | None (alternatywnie data z kalendarza)
    - notes: str (dodatkowe uwagi)
    
    Returns:
    - Reservation object (nowa rezerwacja)
    
    Raises:
    - SlotUnavailableError: Termin jest już zarezerwowany
    
    Database Operations:
    1. SELECT FOR UPDATE TimeSlot (PostgreSQL)
    2. SET is_available=False, reserved_by=user_id
    3. INSERT Reservation
    4. UPDATE OfferStatistics
    5. COMMIT (all-or-nothing)
    
    Side Effects:
    ✅ Generuje Zoom link
    ✅ Aktualizuje statystyki oferty
    
    Algorithm (Race Condition Prevention):
    try:
        slot = TimeSlot.query.filter_by(id, is_available=True).with_for_update().first()
    except:
        # SQLite fallback (dev only)
        slot = TimeSlot.query.filter_by(id, is_available=True).first()
    
    if not slot:
        raise SlotUnavailableError("Termin zajęty")
    
    slot.is_available = False
    db.session.commit()
    """
```

---

### 2. **payment_service.py**

#### `get_access_token()`
```python
def get_access_token():
    """
    Pobranie access tokena z PayPal API.
    
    Environment Variables:
    - PAYPAL_BASE_URL
    - PAYPAL_CLIENT_ID
    - PAYPAL_SECRET / PAYPAL_CLIENT_SECRET
    
    Returns:
    - str (access_token)
    
    HTTP Request:
    POST {PAYPAL_BASE_URL}/v1/oauth2/token
    Headers: Accept: application/json
    Auth: Basic {CLIENT_ID:SECRET}
    Body: grant_type=client_credentials
    
    Response: {"access_token": "..."}
    
    Raises:
    - Exception: PayPal auth failed
    """
```

#### `create_order(amount)`
```python
def create_order(amount):
    """
    Tworzenie zamówienia w PayPal.
    
    Parameters:
    - amount: float (kwota w PLN)
    
    Returns:
    - str (approval URL do redirectu)
    
    HTTP Request:
    POST {PAYPAL_BASE_URL}/v2/checkout/orders
    Headers: Content-Type: application/json, Authorization: Bearer {token}
    Body:
    {
        "intent": "CAPTURE",
        "purchase_units": [{
            "amount": {
                "currency_code": "PLN",
                "value": "{amount}"
            }
        }],
        "application_context": {
            "return_url": "{PAYPAL_RETURN_URL}",
            "cancel_url": "{PAYPAL_CANCEL_URL}"
        }
    }
    
    Response:
    {
        "id": "order_id",
        "links": [
            {"rel": "approve", "href": "https://www.paypal.com/..."}
        ]
    }
    
    Raises:
    - Exception: Order creation failed / No approve link found
    """
```

---

### 3. **email.py**

#### `send_email(to_email, subject, body, html_body=None)`
```python
def send_email(to_email: str, subject: str, body: str, html_body: str = None):
    """
    Wysyłanie emaila via SMTP.
    
    Parameters:
    - to_email: str (odbiorca)
    - subject: str (temat)
    - body: str (treść plain text)
    - html_body: str | None (treść HTML)
    
    Returns:
    - None
    
    Fallback (Dev Mode):
    Jeśli MAIL_USERNAME lub MAIL_PASSWORD brakuje:
    - Wypisuje email do konsoli zamiast wysyłać
    
    SMTP Configuration:
    - Host: {MAIL_SERVER} (default: smtp.gmail.com)
    - Port: {MAIL_PORT} (default: 587)
    - TLS: True
    - User: {MAIL_USERNAME}
    - Pass: {MAIL_PASSWORD}
    
    Email Structure:
    - MIME multipart (plain text + optional HTML)
    - Enkodowanie: UTF-8
    
    Errors:
    - Loguje exception ale nie rzuca błędu
    """
```

#### `send_reservation_confirmation(to_email, reservation)`
```python
def send_reservation_confirmation(to_email: str, reservation):
    """
    Wysłanie emaila potwierdzającego rezerwację.
    
    Parameters:
    - to_email: str
    - reservation: Reservation object
    
    Email Template:
    Subject: ✅ Potwierdzenie rezerwacji — TECH.SERVICES
    
    Contains:
    - Termin spotkania (start_time)
    - Link do Zoom
    - Branding TECH.SERVICES
    
    Includes:
    - Plain text version
    - HTML version (stylized)
    """
```

---

### 4. **zoom.py**

#### `generate_zoom_link(topic, start_time, duration)`
```python
def generate_zoom_link(topic, start_time, duration):
    """
    Generowanie linku do spotkania Zoom.
    
    Parameters:
    - topic: str (nazwa spotkania)
    - start_time: datetime
    - duration: str (minuty)
    
    Returns:
    - str (mock URL - https://zoom.us/j/123456789)
    
    ⚠️ TODO: Implementacja Zoom API
    Environment Variables Required:
    - ZOOM_ACCOUNT_ID
    - ZOOM_CLIENT_ID
    - ZOOM_CLIENT_SECRET
    
    Current Status:
    - Zwraca hardcoded mock URL
    - Loguje parametry do konsoli
    
    Integration Needed:
    - API https://api.zoom.us/v2/users/{userId}/meetings
    - OAuth2 authentication
    """
```

---

### 5. **discord.py**

#### `send_discord_notification(message)`
```python
def send_discord_notification(message):
    """
    Wysłanie powiadomienia na Discord.
    
    Parameters:
    - message: str (treść wiadomości)
    
    Returns:
    - None
    
    Environment Variable:
    - DISCORD_WEBHOOK_URL (Webhook URL kanału)
    
    HTTP Request:
    POST {DISCORD_WEBHOOK_URL}
    Content-Type: application/json
    Body: {"content": message}
    
    Fallback:
    Jeśli webhook URL brakuje - loguje message do konsoli
    """
```

---

### 6. **analysis_service.py**

#### `AnalysisService.identify_optimal_offer()`
```python
@staticmethod
def identify_optimal_offer():
    """
    Generowanie optymalnego bundle'a ofert.
    
    Returns:
    - Offer object (nowa oferta) | None
    
    Algorithm:
    1. Query: all active, non-generated offers
    2. Sort by: reservations_count (descending)
    3. Take: top 2 offers
    4. Combine: name = "Zestaw Korzyści: {offer1} & {offer2}"
    5. Price: 85% of combined (price_from)
    6. Mark: is_generated=True, is_featured=True
    7. Store source IDs: source_offers=[id1, id2] (JSON)
    
    Fallback (Fresh Install):
    Jeśli brak rezerwacji - bierze pierwsze 2 oferty
    
    Returns None if:
    - Mniej niż 2 aktywne oferty
    """
```

#### `AnalysisService.get_market_insights()`
```python
@staticmethod
def get_market_insights():
    """
    Zwraca trendy rynkowe.
    
    Returns:
    - str (insight message)
    
    Logic:
    - Znajdź ofertę z największą liczbą conversions
    - Zwróć info: "Najchętniej wybierany pakiet to '{name}' ({N} zakupów)."
    - Fallback: "Czekamy na pierwsze zamówienia..."
    """
```

---

### 7. **recommender_service.py**

#### `RecommendationService.get_recommendations_for_user(user_id, limit=3)`
```python
@staticmethod
def get_recommendations_for_user(user_id, limit=3):
    """
    Personalizowane rekomendacje na podstawie collaborative filtering.
    
    Parameters:
    - user_id: str
    - limit: int (number of recommendations)
    
    Returns:
    - List[Offer] (lista oferowanych ofert)
    
    Algorithm:
    1. Find offers user already bought (paid reservations)
    2. Find other users who bought the same offers
    3. Find what those users bought (excluding user's purchases)
    4. Rank by frequency (highest count first)
    5. Return top N
    
    Fallbacks:
    - No user history? → Return featured offers
    - No similar users? → Return active offers (not purchased)
    - No recommendations? → Return empty list
    
    SQL Query Pattern:
    SELECT Offer, COUNT(*) as score
    FROM Reservations r
    JOIN Offers o ON r.offer_id = o.id
    WHERE r.user_id IN (similar_user_ids)
      AND o.id NOT IN (user_offer_ids)
      AND o.is_active = True
    GROUP BY Offer
    ORDER BY score DESC
    LIMIT {limit}
    """
```

---

### 8. **invoice_service.py**

#### `InvoiceService.get_next_invoice_number()`
```python
@staticmethod
def get_next_invoice_number():
    """
    Generowanie numeru faktury w formacie FV/YYYY/MM/0001.
    
    Returns:
    - str (invoice number, e.g. "FV/2026/04/0023")
    
    Algorithm:
    1. Get current year/month
    2. Query InvoiceSequence for (year, month)
    3. If not exists: CREATE (year, month, last_value=1)
    4. If exists: INCREMENT last_value
    5. COMMIT (atomic)
    6. Return formatted: FV/{year}/{month:02d}/{last_value:04d}
    
    Database:
    InvoiceSequence (year, month, last_value)
    - Ensures unique numbering per month
    - Atomic transaction prevents duplicates
    """
```

#### `InvoiceService.calculate_vat(gross_amount_cents, vat_rate=23)`
```python
@staticmethod
def calculate_vat(gross_amount_cents, vat_rate=23):
    """
    Obliczanie VAT z kwoty brutto.
    
    Parameters:
    - gross_amount_cents: int (kwota brutto w centach)
    - vat_rate: int (stawka VAT, default 23%)
    
    Returns:
    - Tuple[int, int] (net_amount, vat_amount)
    
    Formula:
    Net = Gross / (1 + Rate%)
    VAT = Gross - Net
    
    Example:
    gross = 10000 (100 PLN)
    vat_rate = 23
    net = 10000 / 1.23 = 8130
    vat = 10000 - 8130 = 1870
    """
```

#### `InvoiceService.generate_invoice_for_payment(payment)`
```python
@staticmethod
def generate_invoice_for_payment(payment):
    """
    Generowanie faktury dla płatności.
    
    Parameters:
    - payment: Payment object
    
    Returns:
    - Invoice object | None
    
    Creates:
    Invoice(
        invoice_number: str (FV/2026/04/0023),
        gross_amount: int (from payment.amount),
        net_amount: int (calculated),
        vat_amount: int (calculated),
        vat_rate: int (23),
        buyer_name: str (user.first_name + last_name),
        ...
    )
    
    TODO:
    - PDF generation (placeholder comment)
    - Store PDF URL
    """
```

---

### 9. **webhook_service.py**

#### `WebhookService.handle_event(data)`
```python
@staticmethod
def handle_event(data):
    """
    Unified handler dla PayPal webhook events.
    
    Supported Events:
    - PAYMENT.CAPTURE.COMPLETED
    - CHECKOUT.ORDER.APPROVED
    - BILLING.SUBSCRIPTION.ACTIVATED
    - BILLING.SUBSCRIPTION.CANCELLED
    
    Parameters:
    - data: dict (webhook payload)
    
    Event Routing:
    - PAYMENT.CAPTURE.COMPLETED → handle_payment_capture()
    - CHECKOUT.ORDER.APPROVED → handle_payment_capture()
    - BILLING.SUBSCRIPTION.ACTIVATED → handle_subscription_status('active')
    - BILLING.SUBSCRIPTION.CANCELLED → handle_subscription_status('cancelled')
    
    Logging: [Webhook] Processing event: {event_type}
    """
```

#### `WebhookService.handle_payment_capture(resource)`
```python
@staticmethod
def handle_payment_capture(resource):
    """
    Obsługa ukończonej płatności.
    
    Parameters:
    - resource: dict (PayPal resource object)
    
    Extracts:
    - order_id z resource.supplementary_data.related_ids.order_id
    
    Calls:
    - handle_successful_payment(order_id, resource)
    
    Error Handling:
    - Logs na console
    - Nie rzuca exception (fire-and-forget)
    """
```

#### `WebhookService.handle_subscription_status(resource, new_status)`
```python
@staticmethod
def handle_subscription_status(resource, new_status):
    """
    Obsługa zmiany statusu subskrypcji.
    
    Parameters:
    - resource: dict (PayPal subscription object)
    - new_status: str ('active' lub 'cancelled')
    
    Updates:
    - Subscription.status = new_status
    
    Logging: [Webhook] Subscription {id} updated to {status}
    """
```

---

## 🔄 Zależności Między Funkcjami

### Dependency Graph

```
┌─────────────────────────────────────────────────────────┐
│                    AUTHENTICATION                        │
├─────────────────────────────────────────────────────────┤
│ register()                                              │
│  ├── valid_email()                                      │
│  ├── valid_password()                                   │
│  ├── User.set_password()                                │
│  └── db.session (COMMIT)                                │
│                                                          │
│ login()                                                 │
│  ├── User.check_password()                              │
│  ├── create_access_token() [JWT]                        │
│  └── db.session (COMMIT)                                │
│                                                          │
│ @jwt_required() decorator                               │
│  └── get_jwt_identity()                                 │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                  OFFERS & RECOMMENDATIONS                │
├─────────────────────────────────────────────────────────┤
│ get_offers()                                            │
│  └── Offer.to_dict()                                    │
│      └── OfferStatistics (via relationship)             │
│                                                          │
│ get_offer(offer_id)                                     │
│  ├── Offer.query.get_or_404()                           │
│  ├── offer.update_stats('view')                         │
│  │   └── OfferStatistics.views += 1                     │
│  └── Offer.to_dict()                                    │
│                                                          │
│ generate_optimal_offer()                                │
│  └── AnalysisService.identify_optimal_offer()          │
│      ├── Query all active offers (sorted by res count)  │
│      ├── Take top 2                                     │
│      └── Create combined offer (85% price, is_generated)
│                                                          │
│ get_insights()                                          │
│  └── AnalysisService.get_market_insights()             │
│      └── Find highest conversions offer                 │
│                                                          │
│ get_recommendations()                                   │
│  └── RecommendationService.get_recommendations_for_user()
│      ├── Find user's purchased offers                   │
│      ├── Find similar users                             │
│      ├── Find what similar users bought                 │
│      └── Rank & return top N                            │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                   RESERVATIONS                           │
├─────────────────────────────────────────────────────────┤
│ create_reservation()                                    │
│  ├── Offer.query.get() [validation]                     │
│  ├── create_reservation_atomic()                        │
│  │   ├── TimeSlot.query.with_for_update() [LOCK]        │
│  │   ├── generate_zoom_link()                           │
│  │   │   └── (TODO Zoom API)                            │
│  │   ├── Reservation() CREATE                           │
│  │   ├── OfferStatistics.update()                       │
│  │   └── db.session.commit() [ATOMIC]                   │
│  ├── User.query.get() [for notification]                │
│  ├── send_email()                                       │
│  │   └── SMTP send (with fallback to console)           │
│  └── send_discord_notification()                        │
│      └── POST Webhook                                   │
│                                                          │
│ get_user_reservations()                                 │
│  └── Reservation.query.filter_by(user_id)              │
│      └── Reservation.to_dict()                          │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                  TIME SLOTS                              │
├─────────────────────────────────────────────────────────┤
│ get_slots()                                             │
│  └── TimeSlot.query.filter()                            │
│      ├── is_available = True                            │
│      ├── reserved_until < now OR null                   │
│      └── optional: filter by week                       │
│                                                          │
│ bulk_create_slots()                                     │
│  └── Loop create TimeSlot()                             │
│      └── db.session.commit()                            │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                   PAYMENTS                               │
├─────────────────────────────────────────────────────────┤
│ create_order()                                          │
│  └── payment_service.create_order()                     │
│      ├── get_access_token()                             │
│      │   └── POST PayPal oauth2/token                   │
│      ├── POST PayPal checkout/orders                    │
│      └── Extract approval_url                           │
│                                                          │
│ [Webhook] handle_event()                                │
│  └── WebhookService.handle_event()                      │
│      ├── Route by event_type                            │
│      ├── handle_payment_capture()                       │
│      │   └── handle_successful_payment() [NOT SHOWN]    │
│      └── handle_subscription_status()                   │
│          └── Subscription.status = new_status           │
│                                                          │
│ generate_invoice_for_payment()                          │
│  ├── get_next_invoice_number()                          │
│  │   └── InvoiceSequence (year, month, last_value)      │
│  ├── calculate_vat()                                    │
│  │   └── Gross / (1 + Rate%) formula                    │
│  └── Invoice() CREATE                                   │
│      └── TODO: PDF generation                           │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                  CONTACT MESSAGES                        │
├─────────────────────────────────────────────────────────┤
│ send_message()                                          │
│  ├── Validate required fields (name, email, message)    │
│  ├── ContactMessage() CREATE                            │
│  ├── db.session.commit()                                │
│  ├── send_email(CONTACT_RECEIVER_EMAIL, ...)            │
│  │   └── SMTP send                                      │
│  └── return 201                                         │
│                                                          │
│ get_messages()                                          │
│  └── ContactMessage.query.order_by(created_at DESC)     │
└─────────────────────────────────────────────────────────┘
```

### Call Chain Example: Create Reservation

```
Browser Client
    │
    ├─ POST /api/reservations
    │  (with Authorization header: "Bearer {token}")
    │
    ▼
create_reservation() [routes/reservations.py]
    │
    ├─ @jwt_required()
    │  └─ get_jwt_identity() → user_id
    │
    ├─ Validate offer_id exists
    │  └─ Offer.query.get(offer_id)
    │
    ├─ create_reservation_atomic(
    │      user_id, offer_id, time_slot_id, manual_datetime, notes
    │  )
    │  └─ [services/reservation_service.py]
    │     ├─ TimeSlot.query.with_for_update() [LOCK]
    │     ├─ generate_zoom_link(...) [services/zoom.py]
    │     ├─ Reservation() CREATE
    │     ├─ OfferStatistics.update()
    │     └─ db.session.commit() ✓ ATOMIC
    │
    ├─ send_email(user.email, ...) [services/email.py]
    │  ├─ Connect SMTP
    │  └─ Send (or print to console if DEV)
    │
    ├─ send_discord_notification(...) [services/discord.py]
    │  └─ POST Discord Webhook
    │
    └─ return 201 + {message, reservation_id, meeting_link}
```

---

## ⚙️ Configuration & Extensions

### extensions.py - Flask Extensions Init

```python
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_limiter import Limiter

db = SQLAlchemy()              # Database ORM
migrate = Migrate()             # Migration tool
cors = CORS()                   # CORS handler
jwt = JWTManager()              # JWT auth
mail = Mail()                   # Email sender
limiter = Limiter(
    key_func=get_remote_address  # Rate limiting by IP
)
```

### app.py - Flask Configuration

#### Key Configuration

```python
SQLALCHEMY_DATABASE_URI = sqlite:////var/www/techservices/backend-techservices/instance/app.db
# (or via environment: DATABASE_URL)

SQLALCHEMY_TRACK_MODIFICATIONS = False

SECRET_KEY = {from env or 'dev-secret-key'}

JWT_SECRET_KEY = {from env or 'jwt-dev-key'}
JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 hours

# MAIL Config
MAIL_SERVER = smtp.gmail.com
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = {from env}
MAIL_PASSWORD = {from env}
MAIL_DEFAULT_SENDER = {from env or 'noreply@techservices.com.pl'}

# Rate Limiting
RATELIMIT_DEFAULT = "100 per minute"
RATELIMIT_STORAGE_URI = "memory://"

# CORS
origins = [
    "https://techservices.com.pl",
    "https://www.techservices.com.pl",
    "http://localhost:5173",
    "http://localhost:3000"
]
```

#### Extensions Initialization

```python
db.init_app(app)
migrate.init_app(app, db)
jwt.init_app(app)
mail.init_app(app)
limiter.init_app(app)
cors.init_app(app, resources={r"/api/*": {...}})
```

#### Blueprints Registration

```python
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(offers_bp, url_prefix='/api/offers')
app.register_blueprint(reservation_bp, url_prefix='/api/reservations')
app.register_blueprint(slots_bp, url_prefix='/api/slots')
app.register_blueprint(user_bp, url_prefix='/api/user')
app.register_blueprint(contact_bp, url_prefix='/api/contact')
app.register_blueprint(payment_bp, url_prefix='/api/payments')
```

### Environment Variables (.env)

```bash
# Flask
FLASK_ENV=production|development
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-key-here

# Database
DATABASE_URL=postgresql://user:pass@localhost/techservices
# or: sqlite:///instance/app.db

# Email (Gmail SMTP)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password  # NOT regular password
MAIL_DEFAULT_SENDER=noreply@techservices.com.pl
CONTACT_RECEIVER_EMAIL=igorzajq0@gmail.com

# PayPal
PAYPAL_BASE_URL=https://api-m.sandbox.paypal.com  # or production
PAYPAL_CLIENT_ID=your-client-id
PAYPAL_SECRET=your-secret
PAYPAL_RETURN_URL=https://techservices.com.pl/payment/success
PAYPAL_CANCEL_URL=https://techservices.com.pl/payment/cancel

# Discord
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# Zoom (TODO)
ZOOM_ACCOUNT_ID=your-account-id
ZOOM_CLIENT_ID=your-client-id
ZOOM_CLIENT_SECRET=your-secret
```

---

## 🚀 Deployment Configuration

### deployment/techservices.nginx

```nginx
server {
    listen 443 ssl http2;
    server_name techservices.com.pl www.techservices.com.pl;

    # SSL config
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Reverse proxy to Gunicorn
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static frontend
    location / {
        root /var/www/techservices/frontend;
        try_files $uri $uri/ /index.html;
    }
}
```

### deployment/techservices.service

```ini
[Unit]
Description=TechServices Flask Backend
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/var/www/techservices/backend
Environment="PATH=/var/www/techservices/backend/venv/bin"
ExecStart=/var/www/techservices/backend/venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:5000 \
    --timeout 60 \
    app:app

[Install]
WantedBy=multi-user.target
```

---

## ⚠️ Problemy & TODO

### 🔴 KRYTYCZNE PROBLEMY

1. **Zoom API niezaimplementowana**
   - Plik: `services/zoom.py`
   - Status: Mock URL (https://zoom.us/j/123456789)
   - TODO: Implementacja API z ZOOM_ACCOUNT_ID, ZOOM_CLIENT_ID
   - Wpływ: Linki do spotkań są fikcyjne!

2. **PayPal Payment Capture Incomplete**
   - Funkcja `handle_successful_payment()` nie znaleziona!
   - Webhook przychodzi, ale aktualizacja statusu rezerwacji brakuje
   - Rezerwacje nigdy nie zmienią status na "paid"

3. **Email Verification Wyłączona**
   - Użytkownicy automatycznie zweryfikowani (is_verified=True)
   - Endpoint `/verify/<token>` istnieje ale nieużywany
   - SMTP error 535 został obejść, ale brak emaili weryfikacyjnych

### 🟡 WAŻNE TODO

4. **Invoice PDF Generation**
   - Plik: `services/invoice_service.py`
   - Status: Comment placeholder ("TODO: PDF generation")
   - Faktury bez PDF!

5. **Reset Password Niekompletne**
   - Plik: `routes/auth.py` / `reset_password()`
   - Email system later (placeholder pass)
   - Brakuje wysyłki linku resetującego

6. **Rate Limiter Cache**
   - Skonfigurowany na memory:// (dev only)
   - Production powinien używać Redis

### 🟠 OPTYMALIZACJA

7. **N+1 Query Problem**
   - `get_offers()` - nie ma eager loading dla statistics
   - Każda oferta trigger oddzielny query

8. **Transaction Isolation**
   - SQLite nie wspiera SELECT FOR UPDATE
   - Race condition w `create_reservation_atomic()` w dev

9. **Brakujące Error Handlers**
   - Brak global error handler dla Flask
   - Brak validation schematów (JSON input validation)

### 📝 DOKUMENTACJA

10. **API Dokumentacja**
    - Brak OpenAPI/Swagger
    - Brak Postman collection

11. **Code Comments**
    - Są, ale niepełne w service'ach
    - Brakuje docstrings w niektórych metodach

### 🧪 TESTOWANIE

12. **Tests Brakuje**
    - Brak unit testów
    - Brak integration testów
    - Brak test fixtures

13. **Pliki Testowe Niekompletne**
    - `test_delete.py` - test usuwania (?)
    - `check_db.py` - health check (?)

---

## 📊 Statystyki Projektu

| Metryka | Wartość |
|---------|---------|
| Liczba Modeli | 12 |
| Liczba Routes | 7 |
| Liczba Services | 9 |
| API Endpoints | ~30 |
| Functions/Methods | ~50+ |
| Lines of Code | ~2000+ |
| Dependencies | 14 |
| Database Tables | 12 |

---

## 🎯 Rekomendacje

### Priorytet 1 (TERAZ)
1. ✅ Implementuj Zoom API
2. ✅ Dokończ `handle_successful_payment()`
3. ✅ Dodaj PDF invoice generation

### Priorytet 2 (TYDZIEŃ)
4. Implementuj reset password
5. Dodaj JSON schema validation
6. Skonfiguruj Redis dla production
7. Implementuj global error handler

### Priorytet 3 (MIESIĄC)
8. Napraw N+1 queries
9. Napisz test suite
10. Dodaj OpenAPI documentation
11. Optymalizuj queries z EXPLAIN

### Priorytet 4 (BACKLOG)
12. Implementuj webhook signatures verification
13. Dodaj audit logging
14. Implementuj soft deletes
15. Skalowanie (multi-tenant optimization)

---

## 📞 Kontakt & Notatki

**Status**: Backend w stanie beta  
**Ostatnia Aktualizacja**: 29.04.2026  
**Autor Audytu**: Copilot  
**Zatwierdzono**: -

---

**Koniec Raportu**
