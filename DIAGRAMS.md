# 🎨 DIAGRAMY ARCHITEKTURY

## 1. System Architecture Diagram

```mermaid
graph TB
    subgraph Client["🌐 Klient"]
        Browser["🖥️ Przeglądarka"]
        Mobile["📱 Aplikacja Mobile"]
    end

    subgraph Frontend["⚛️ Frontend"]
        AdminApp["Admin Panel<br/>(React/Vite)"]
        UserApp["User App<br/>(React/Vite)"]
    end

    subgraph LoadBalancer["🔄 Load Balancer"]
        Nginx["Nginx<br/>Reverse Proxy<br/>Port 443 SSL"]
    end

    subgraph BackendServers["🚀 Backend Servers"]
        Gunicorn1["Gunicorn<br/>Port 5000<br/>Workers: 4"]
        Gunicorn2["Gunicorn<br/>Port 5001<br/>Workers: 4"]
    end

    subgraph FlaskApp["🐍 Flask Application"]
        App["app.py<br/>Flask(app)"]
        Routes["Routes<br/>Blueprints<br>/api/*"]
        Services["Services<br/>Business Logic"]
        Models["ORM Models<br/>SQLAlchemy"]
    end

    subgraph Extensions["🔧 Extensions"]
        DB["📊 SQLAlchemy<br/>Database"]
        JWT["🔐 JWT Auth<br/>Flask-JWT"]
        Mail["📧 Mail<br/>Flask-Mail"]
        CORS["🌐 CORS<br/>Flask-CORS"]
        Limiter["⏱️ Rate Limiter<br/>Flask-Limiter"]
    end

    subgraph DataLayer["💾 Data Layer"]
        PostgreSQL["🐘 PostgreSQL<br/>(Production)"]
        SQLite["📄 SQLite<br/>(Development)"]
    end

    subgraph ExternalServices["🌍 External Services"]
        PayPal["💳 PayPal API<br/>Payments"]
        Zoom["📹 Zoom API<br/>Meetings"]
        Gmail["📧 Gmail SMTP<br/>Emails"]
        Discord["💬 Discord<br/>Webhooks"]
    end

    subgraph Cache["⚡ Cache & Queue"]
        Redis["🔴 Redis<br/>Cache/Queue<br/>(Optional)"]
        Celery["🌾 Celery<br/>Async Tasks<br/>(Optional)"]
    end

    Browser -->|HTTPS| Nginx
    Mobile -->|HTTPS| Nginx
    AdminApp -->|HTTPS| Nginx
    UserApp -->|HTTPS| Nginx
    
    Nginx -->|load balance| Gunicorn1
    Nginx -->|load balance| Gunicorn2
    
    Gunicorn1 --> App
    Gunicorn2 --> App
    
    App --> Routes
    Routes --> Services
    Services --> Models
    
    Models --> DB
    App --> JWT
    Routes --> Limiter
    App --> Mail
    App --> CORS
    
    DB -->|read/write| PostgreSQL
    DB -->|dev| SQLite
    
    Services -->|API calls| PayPal
    Services -->|API calls| Zoom
    Services -->|SMTP| Gmail
    Services -->|Webhook| Discord
    
    Services -->|cache/queue| Redis
    Services -->|async| Celery
```

---

## 2. Database Entity Relationship Diagram

```mermaid
erDiagram
    USERS ||--o{ RESERVATIONS : "has"
    USERS ||--o{ SUBSCRIPTIONS : "has"
    USERS ||--o{ CONNECTED_ACCOUNTS : "has"
    USERS ||--o{ INVOICES : "made by"
    USERS }o--|| TENANTS : "belongs to"
    
    OFFERS ||--o{ RESERVATIONS : "has"
    OFFERS ||--|| OFFER_STATISTICS : "has"
    
    TIMESLOTS ||--o{ RESERVATIONS : "booked via"
    TIMESLOTS }o--|| USERS : "reserved by"
    
    RESERVATIONS ||--o{ PAYMENTS : "requires"
    RESERVATIONS ||--o{ INVOICES : "generates"
    
    PAYMENTS ||--|| INVOICES : "creates"
    
    TENANTS ||--o{ USERS : "has many"
    TENANTS ||--o{ OFFERS : "has many"
    TENANTS ||--o{ INVOICES : "issues"
    
    COUPONS ||--o{ RESERVATIONS : "applied to"
    
    SUBSCRIPTION_PLANS ||--o{ SUBSCRIPTIONS : "defines"
    
    CONTACT_MESSAGES ||--o{ USERS : "from"
    
    INVOICE_SEQUENCE ||--o{ INVOICES : "increments for"
```

---

## 3. API Routes Hierarchy

```mermaid
graph TD
    API["/api<br/>Root"]
    
    API --> Auth["/api/auth<br/>Authentication"]
    API --> Offers["/api/offers<br/>Offers Management"]
    API --> Reservations["/api/reservations<br/>Reservations"]
    API --> Slots["/api/slots<br/>Time Slots"]
    API --> User["/api/user<br/>User Management"]
    API --> Contact["/api/contact<br/>Contact Form"]
    API --> Payments["/api/payments<br/>Payments"]
    
    Auth -->|POST| Register["register<br/>Create new user"]
    Auth -->|POST| Login["login<br/>Get JWT token"]
    Auth -->|GET| Me["me<br/>Current user info"]
    Auth -->|POST| Logout["logout<br/>Invalidate session"]
    Auth -->|GET| Verify["verify/token<br/>Email verification"]
    Auth -->|POST| ResetPwd["reset-password<br/>Password recovery"]
    
    Offers -->|GET| OffersList["/ <br/>All offers"]
    Offers -->|GET| OfferDetail["/offer_id<br/>Offer details"]
    Offers -->|POST| OfferCreate["/Create new"]
    Offers -->|PUT| OfferUpdate["/:id Update"]
    Offers -->|PATCH| OfferToggle["/:id/toggle"]
    Offers -->|DELETE| OfferDelete["/:id Delete"]
    Offers -->|POST| GenOffer["/generate-optimal<br/>AI bundle"]
    Offers -->|GET| Insights["/insights<br/>Market trends"]
    Offers -->|GET| Recommend["/recommendations<br/>For user"]
    
    Reservations -->|POST| ResCreate["/ Create"]
    Reservations -->|GET| ResAll["/ All"]
    Reservations -->|GET| ResUser["/user/:id User"]
    Reservations -->|PATCH| ResStatus["/:id/status"]
    Reservations -->|PATCH| ResCancel["/:id/cancel"]
    
    Slots -->|GET| SlotList["/ Available"]
    Slots -->|POST| SlotCreate["/Create"]
    Slots -->|DELETE| SlotDelete["/:id Delete"]
    Slots -->|POST| SlotBulk["/bulk Batch"]
    
    User -->|GET| Profile["/profile"]
    User -->|PUT| ProfileUpdate["/profile Update"]
    User -->|GET| MyRes["/reservations"]
    User -->|GET| AllUsers["/all Admin"]
    
    Contact -->|POST| ContactSend["/ Send message"]
    Contact -->|GET| ContactList["/List all"]
    Contact -->|PATCH| ContactStatus["/:id/status"]
    
    Payments -->|POST| PaymentCreate["/create-order"]
    Payments -->|GET| Invoices["/invoices"]
    
    classDef public fill:#90EE90
    classDef protected fill:#FFB6C1
    classDef admin fill:#FF6347
    classDef external fill:#87CEEB
    
    class OffersList,OfferDetail,ResUser,Insights,Recommend,Slot* public
    class Me,Profile,MyRes,ContactSend protected
    class Register,Login,Logout,Auth,OfferCreate,OfferUpdate,Offerings,ResCreate,ResAll,ProfileUpdate,AllUsers,ContactList admin
    class PaymentCreate,Invoices external
```

---

## 4. Request Flow - Create Reservation

```mermaid
sequenceDiagram
    participant Client as 🖥️ Client
    participant Route as 🛣️ Route Handler
    participant Service as 🔧 Service
    participant DB as 💾 Database
    participant Zoom as 📹 Zoom API
    participant Email as 📧 Email
    participant Discord as 💬 Discord

    Client->>Route: POST /api/reservations<br/>offer_id, time_slot_id
    activate Route

    Route->>Route: @jwt_required() ✓
    Route->>Route: get_jwt_identity() → user_id

    Route->>DB: SELECT Offer WHERE id=?
    activate DB
    DB-->>Route: offer (or 404)
    deactivate DB

    Route->>Service: create_reservation_atomic(...)
    activate Service

    Service->>DB: BEGIN TRANSACTION
    Service->>DB: SELECT TimeSlot WHERE id WITH FOR UPDATE
    activate DB
    DB-->>Service: slot (locked)
    
    alt Slot not available
        DB-->>Service: NULL
        Service-->>Route: SlotUnavailableError 409
    else Slot available
        Service->>Service: generate_zoom_link(...)
        activate Service
        Service->>Zoom: POST /meetings (TODO)
        Zoom-->>Service: zoom_url
        Service-->>Service: https://zoom.us/j/123456789
        deactivate Service

        Service->>DB: INSERT Reservation
        Service->>DB: UPDATE TimeSlot (is_available=False)
        Service->>DB: UPDATE OfferStatistics (++count)
        Service->>DB: COMMIT
        deactivate DB

        Service-->>Route: reservation object
    end
    deactivate Service

    Route->>DB: SELECT User WHERE id=?
    activate DB
    DB-->>Route: user
    deactivate DB

    Route->>Email: send_email(user.email, ...)
    activate Email
    Email->>Email: SMTP connect
    Email->>Email: send message
    Email-->>Route: ✓ sent (or logged)
    deactivate Email

    Route->>Discord: send_discord_notification(...)
    activate Discord
    Discord->>Discord: POST webhook
    Discord-->>Route: ✓ sent
    deactivate Discord

    Route-->>Client: 201 Created<br/>{message, reservation_id, meeting_link}
    deactivate Route
```

---

## 5. Authentication & Authorization Flow

```mermaid
graph LR
    subgraph Auth["🔐 Authentication"]
        Register["1. Register<br/>User"]
        VerifyEmail["2. Verify Email<br/>(Skipped)"]
        Login["3. Login<br/>Email + Password"]
        GetToken["4. Get JWT Token<br/>24h expiry"]
    end
    
    subgraph Protected["🛡️ Protected Routes"]
        Check["Check Token<br/>@jwt_required()"]
        Validate["Validate Signature"]
        Extract["Extract user_id"]
        Route["Route Handler"]
    end
    
    subgraph Storage["💾 Token Storage"]
        LocalStorage["LocalStorage<br/>(Frontend)"]
        Header["Authorization Header<br/>Bearer token"]
    end
    
    Register -->|is_verified=True| VerifyEmail
    VerifyEmail -->|Auto-approved| Login
    Login -->|valid credentials| GetToken
    GetToken -->|eyJ0e...| LocalStorage
    LocalStorage -->|every request| Header
    Header -->|Bearer eyJ...| Check
    Check -->|valid| Validate
    Validate -->|signature ok| Extract
    Extract -->|user_id| Route
    Route -->|business logic| Protected
    
    style Auth fill:#90EE90
    style Protected fill:#FFB6C1
    style Storage fill:#87CEEB
```

---

## 6. Payment Flow (PayPal Integration)

```mermaid
sequenceDiagram
    participant User as 👤 User
    participant Frontend as 🌐 Frontend
    participant Backend as 🐍 Backend
    participant PayPal as 💳 PayPal
    participant Webhook as 🔔 Webhook

    User->>Frontend: Click "Pay Now"
    Frontend->>Backend: POST /api/payments/create-order<br/>{amount: 5000}
    activate Backend

    Backend->>Backend: payment_service.create_order()
    Backend->>Backend: get_access_token()
    Backend->>PayPal: POST oauth2/token
    PayPal-->>Backend: {access_token: "..."}

    Backend->>PayPal: POST checkout/orders
    PayPal-->>Backend: {links: [{rel: approve, href: "..."}]}
    Backend-->>Frontend: 200 {approval_url: "https://paypal.com/..."}
    deactivate Backend

    Frontend->>PayPal: Redirect to approval_url
    User->>PayPal: Approve payment
    PayPal->>Frontend: Redirect to return_url ✓

    activate Backend
    par Webhook Processing
        PayPal->>Webhook: POST /webhook<br/>PAYMENT.CAPTURE.COMPLETED
        Webhook->>Backend: WebhookService.handle_event()
        Backend->>Backend: handle_payment_capture()
        Backend->>Backend: handle_successful_payment()
        Note right of Backend: ⚠️ NOT IMPLEMENTED!
    end
    
    Backend-->>Backend: Update Reservation.payment_status='paid'
    Backend-->>Backend: Generate Invoice
    Backend-->>Backend: Send confirmation email
    deactivate Backend

    Frontend->>User: ✅ Payment Success
```

---

## 7. Service Dependencies

```mermaid
graph TB
    subgraph API["API Routes"]
        auth["auth.py"]
        offers["offers.py"]
        reservations["reservations.py"]
        slots["slots.py"]
        user["user.py"]
        contact["contact.py"]
        payment["payment.py"]
    end
    
    subgraph Services["Business Services"]
        res_svc["reservation_service<br/>create_reservation_atomic"]
        pay_svc["payment_service<br/>create_order"]
        email_svc["email.py<br/>send_email"]
        zoom_svc["zoom.py<br/>generate_zoom_link"]
        discord_svc["discord.py<br/>send_discord"]
        analysis_svc["analysis_service<br/>identify_optimal"]
        rec_svc["recommender_service<br/>get_recommendations"]
        invoice_svc["invoice_service<br/>generate_invoice"]
        webhook_svc["webhook_service<br/>handle_event"]
    end
    
    subgraph Models["Data Layer"]
        user_model["User"]
        offer_model["Offer"]
        res_model["Reservation"]
        slot_model["TimeSlot"]
        stats_model["OfferStatistics"]
        payment_model["Payment"]
        invoice_model["Invoice"]
    end
    
    subgraph External["🌍 External"]
        paypal["PayPal API"]
        zoom["Zoom API"]
        gmail["Gmail SMTP"]
        discord_api["Discord API"]
    end
    
    auth --> email_svc
    offers --> analysis_svc
    offers --> rec_svc
    reservations --> res_svc
    reservations --> email_svc
    reservations --> discord_svc
    payment --> pay_svc
    payment --> invoice_svc
    
    res_svc --> zoom_svc
    res_svc --> stats_model
    res_svc --> slot_model
    
    pay_svc --> paypal
    
    email_svc --> gmail
    zoom_svc --> zoom
    discord_svc --> discord_api
    
    res_svc --> res_model
    res_svc --> user_model
    res_svc --> offer_model
    
    analysis_svc --> offer_model
    analysis_svc --> res_model
    rec_svc --> res_model
    rec_svc --> offer_model
    
    invoice_svc --> payment_model
    invoice_svc --> invoice_model
    
    webhook_svc --> payment_model
```

---

## 8. Database Connection & Session Management

```mermaid
graph TD
    App["Flask App<br/>create_app()"]
    
    subgraph Config["Configuration"]
        DbUri["DATABASE_URL<br/>or sqlite"]
        SecretKey["SECRET_KEY"]
        JwtSecret["JWT_SECRET_KEY"]
    end
    
    subgraph Init["Initialization"]
        DbInit["db.init_app(app)"]
        MigrateInit["migrate.init_app(app)"]
        JwtInit["jwt.init_app(app)"]
        MailInit["mail.init_app(app)"]
        LimiterInit["limiter.init_app(app)"]
    end
    
    subgraph Connection["Database Connection"]
        SQLAlchemy["SQLAlchemy<br/>Connection Pool"]
        PgSQL["PostgreSQL<br/>(prod)"]
        SQLite["SQLite<br/>(dev)"]
    end
    
    subgraph Context["Application Context"]
        AppContext["with app.app_context()"]
        CreateAll["db.create_all()"]
        Migrate["db.migrate()"]
    end
    
    App --> Config
    App --> Init
    Init --> DbInit
    DbInit --> Connection
    Connection --> PgSQL
    Connection --> SQLite
    App --> Context
    Context --> CreateAll
    Context --> Migrate
    
    classDef config fill:#FFE4B5
    classDef init fill:#DDA0DD
    classDef connection fill:#ADD8E6
    classDef context fill:#98FB98
    
    class Config config
    class Init init
    class Connection connection
    class Context context
```

---

## 9. Rate Limiting & Request Flow

```mermaid
graph LR
    Request["📥 Incoming Request"]
    
    subgraph RateLimit["Rate Limiter Check"]
        IP["Get Client IP"]
        Check["Check Rate Limit<br/>100 per minute"]
        Allow{"Within Limit?"}
    end
    
    subgraph Auth["Authentication"]
        JWT["Parse JWT Token"]
        Verify["Verify Signature"]
        Extract["Extract Payload"]
    end
    
    subgraph Validation["Validation"]
        Schema["Validate Schema<br/>(TODO)"]
        Business["Business Rules"]
    end
    
    subgraph Handler["Route Handler"]
        Logic["Business Logic"]
        Db["Database Query"]
        External["External API"]
    end
    
    subgraph Response["Response"]
        Serialize["Serialize Data"]
        Status["HTTP Status"]
        Send["Send Response"]
    end
    
    subgraph Error["Error Handling"]
        Catch["Catch Exception"]
        Log["Log Error"]
        ClientErr["Return Error Response"]
    end
    
    Request --> RateLimit
    RateLimit --> IP
    IP --> Check
    Check --> Allow
    
    Allow -->|Yes| Auth
    Allow -->|No| Response
    
    Auth --> JWT
    JWT --> Verify
    Verify -->|Valid| Extract
    Extract --> Validation
    
    Verify -->|Invalid| Error
    
    Validation --> Schema
    Schema --> Business
    Business --> Handler
    
    Handler --> Logic
    Logic --> Db
    Db --> External
    External --> Response
    
    Handler -.->|Error| Error
    
    Error --> Catch
    Catch --> Log
    Log --> ClientErr
    ClientErr --> Send
    
    Response --> Serialize
    Serialize --> Status
    Status --> Send
    
    Send --> Response2["✅ Response to Client"]
    
    classDef limiter fill:#FFB6C1
    classDef auth fill:#FFA500
    classDef validation fill:#87CEEB
    classDef handler fill:#98FB98
    classDef response fill:#DDA0DD
    classDef error fill:#FF6347
    
    class RateLimit limiter
    class Auth auth
    class Validation validation
    class Handler handler
    class Response response
    class Error error
```

---

**Wygenerowano**: 29.04.2026  
**Format**: Mermaid Diagrams
