# System Architecture Diagram

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                            │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────────┐ │
│  │ File Upload │  │ Risk Display │  │ Statistics Dashboard    │ │
│  │ (Drag/Drop) │  │ (CIA Scores) │  │ (Scan History)          │ │
│  └─────────────┘  └──────────────┘  └─────────────────────────┘ │
│         HTML/CSS/JavaScript - Responsive Web Interface            │
└──────────────────────┬───────────────────────────────────────────┘
                       │ HTTP/REST API
                       ↓
┌──────────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND SERVER                         │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ API Endpoints                                               │ │
│  │  • POST /api/upload          • GET /api/report/{id}       │ │
│  │  • GET  /api/history         • GET /api/stats             │ │
│  │  • GET  /api/export/{id}     • GET /health                │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │ Request      │  │ Validation   │  │ Error Handling         │ │
│  │ Validation   │  │ (Pydantic)   │  │ & Logging              │ │
│  └──────────────┘  └──────────────┘  └────────────────────────┘ │
└──────────────────────┬───────────────────────────────────────────┘
                       │
                       ↓
┌──────────────────────────────────────────────────────────────────┐
│                     SERVICE LAYER                                 │
│  ┌────────────────────────┐  ┌────────────────────────────────┐ │
│  │  Analysis Service      │  │  Database Service              │ │
│  │  • Coordinate workflow │  │  • CRUD operations             │ │
│  │  • Generate scan IDs   │  │  • Stats aggregation           │ │
│  │  • Error handling      │  │  • Audit logging               │ │
│  └────────────────────────┘  └────────────────────────────────┘ │
└──────────┬────────────────────────────────┬──────────────────────┘
           │                                │
           ↓                                ↓
┌──────────────────────────┐    ┌──────────────────────────────────┐
│ FEATURE EXTRACTION       │    │   DATABASE LAYER                 │
│  ┌───────────────────┐   │    │  ┌────────────────────────────┐ │
│  │ Androguard        │   │    │  │ SQLAlchemy ORM             │ │
│  │ • APK Parsing     │   │    │  │ • ScanResult               │ │
│  │ • DEX Analysis    │   │    │  │ • SystemStats              │ │
│  └───────────────────┘   │    │  │ • AuditLog                 │ │
│  ┌───────────────────┐   │    │  └────────────────────────────┘ │
│  │ Feature Extractor │   │    │  ┌────────────────────────────┐ │
│  │ • Permissions     │   │    │  │ SQLite (Development)       │ │
│  │ • API Calls       │   │    │  │ ShaktiDB (Production)      │ │
│  │ • Intents         │   │    │  └────────────────────────────┘ │
│  │ • Metadata        │   │    └──────────────────────────────────┘
│  └───────────────────┘   │
└────────────┬─────────────┘
             │
             ↓
┌──────────────────────────────────────────────────────────────────┐
│               MACHINE LEARNING MODEL SERVICE                      │
│  ┌──────────────────────┐  ┌──────────────────────────────────┐ │
│  │ Pre-trained Model    │  │ Model Components                 │ │
│  │ • Random Forest      │  │ • StandardScaler                 │ │
│  │ • XGBoost            │  │ • Feature Vector Builder         │ │
│  │ • Gradient Boosting  │  │ • Prediction Pipeline            │ │
│  └──────────────────────┘  └──────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Training Pipeline (Offline)                                │ │
│  │ • MH-100K Dataset (101,975 samples)                        │ │
│  │ • SMOTE Class Balancing                                    │ │
│  │ • Cross-validation                                         │ │
│  │ • Model Selection & Persistence                            │ │
│  └────────────────────────────────────────────────────────────┘ │
└────────────┬─────────────────────────────────────────────────────┘
             │ Prediction + Confidence
             ↓
┌──────────────────────────────────────────────────────────────────┐
│              NIST CIA RISK SCORING ENGINE                         │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Confidentiality Analysis                                   │ │
│  │ • Privacy-invasive permissions (location, contacts, etc.)  │ │
│  │ • Data access API calls                                    │ │
│  │ • Information leakage patterns                             │ │
│  │ Weight: 35%                                                │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Integrity Analysis                                         │ │
│  │ • System modification permissions                          │ │
│  │ • Code injection patterns (DexClassLoader, Runtime.exec)   │ │
│  │ • Package installation capabilities                        │ │
│  │ Weight: 35%                                                │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Availability Analysis                                      │ │
│  │ • Resource consumption (wake locks, battery)               │ │
│  │ • Background process control                               │ │
│  │ • Service disruption capabilities                          │ │
│  │ Weight: 30%                                                │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Risk Level Determination                                   │ │
│  │ SAFE (0-19) | LOW (20-39) | MEDIUM (40-59) |              │ │
│  │ HIGH (60-79) | CRITICAL (80-100)                           │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Output Generation                                          │ │
│  │ • Threat indicators                                        │ │
│  │ • Security recommendations                                 │ │
│  │ • Comprehensive risk report                                │ │
│  └────────────────────────────────────────────────────────────┘ │
└────────────┬─────────────────────────────────────────────────────┘
             │
             ↓
┌──────────────────────────────────────────────────────────────────┐
│                   LOGGING & MONITORING                            │
│  ┌────────────────────────┐  ┌────────────────────────────────┐ │
│  │ Application Logs       │  │ Audit Trail                    │ │
│  │ • loguru logger        │  │ • User actions                 │ │
│  │ • Rotating files       │  │ • Scan operations              │ │
│  │ • Error tracking       │  │ • System events                │ │
│  └────────────────────────┘  └────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

```
┌─────────┐
│  User   │
│ Uploads │
│   APK   │
└────┬────┘
     │
     ↓
┌────────────────┐
│ 1. Validation  │  ✓ File extension (.apk)
│    & Storage   │  ✓ File size (<100MB)
└────┬───────────┘  ✓ Save to uploads/
     │
     ↓
┌────────────────────┐
│ 2. Feature         │  → Permissions (166 types)
│    Extraction      │  → API Calls (24,417+ methods)
│    (Androguard)    │  → Intents (250 types)
└────┬───────────────┘  → Metadata (hash, package, etc.)
     │
     ↓
┌────────────────────┐
│ 3. ML Prediction   │  → Load trained model
│    (scikit-learn)  │  → Scale features
└────┬───────────────┘  → Predict: Benign/Malware
     │                   → Confidence score
     ↓
┌────────────────────┐
│ 4. Risk Scoring    │  → Confidentiality: 0-100
│    (NIST CIA)      │  → Integrity: 0-100
└────┬───────────────┘  → Availability: 0-100
     │                   → Overall: 0-100
     ↓                   → Risk Level: SAFE/LOW/MEDIUM/HIGH/CRITICAL
┌────────────────────┐
│ 5. Report          │  → Threat indicators
│    Generation      │  → Security recommendations
└────┬───────────────┘  → Feature counts
     │                   → CIA analysis
     ↓
┌────────────────────┐
│ 6. Database        │  → Save scan result
│    Storage         │  → Update statistics
└────┬───────────────┘  → Create audit log
     │
     ↓
┌────────────────────┐
│ 7. Response to     │  → Display results
│    User Interface  │  → Show risk scores
└────────────────────┘  → Provide recommendations
```

## Component Interactions

```
┌──────────────┐     upload_file()     ┌──────────────┐
│   Frontend   │ ───────────────────→  │   Backend    │
│   (HTML/JS)  │ ←─────────────────── │   (FastAPI)  │
└──────────────┘     return_results    └──────┬───────┘
                                              │
                                              │ analyze_apk()
                                              ↓
                               ┌──────────────────────────┐
                               │  Analysis Service        │
                               │  • Coordinate workflow   │
                               │  • Call extractors       │
                               │  • Aggregate results     │
                               └──────┬──────────┬────────┘
                                      │          │
           extract_features()         │          │ predict()
                  ┌───────────────────┘          └──────────────────┐
                  ↓                                                  ↓
         ┌────────────────┐                              ┌────────────────┐
         │   Feature      │                              │   ML Model     │
         │   Extractor    │                              │   Service      │
         │ (Androguard)   │                              │ (scikit-learn) │
         └────────┬───────┘                              └────────┬───────┘
                  │                                               │
                  │ features_dict                                 │ prediction
                  └───────────────────┬───────────────────────────┘
                                      ↓
                          ┌───────────────────────┐
                          │  Risk Scorer          │
                          │  (NIST CIA Framework) │
                          └───────────┬───────────┘
                                      │
                                      │ risk_report
                                      ↓
                          ┌───────────────────────┐
                          │  Database Service     │
                          │  • Save results       │
                          │  • Update stats       │
                          │  • Create audit log   │
                          └───────────────────────┘
```

## Security Flow

```
┌─────────────────────────────────────────────────────────┐
│                   SECURITY LAYERS                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Layer 1: Input Validation                             │
│  ├─ File extension check (.apk only)                   │
│  ├─ File size limit (100MB)                            │
│  └─ MIME type validation                               │
│                                                         │
│  Layer 2: Request Validation                           │
│  ├─ Pydantic schema validation                         │
│  ├─ SQL injection prevention (ORM)                     │
│  └─ CORS policy enforcement                            │
│                                                         │
│  Layer 3: Analysis Isolation                           │
│  ├─ Temporary file storage                             │
│  ├─ Error handling & recovery                          │
│  └─ Resource limits                                    │
│                                                         │
│  Layer 4: Data Sanitization                            │
│  ├─ XSS prevention in outputs                          │
│  ├─ JSON encoding                                      │
│  └─ Safe error messages                                │
│                                                         │
│  Layer 5: Audit & Logging                              │
│  ├─ User action tracking                               │
│  ├─ Scan history                                       │
│  └─ Error logging                                      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Deployment Architecture

```
                    ┌─────────────────┐
                    │   Load Balancer │
                    │     (nginx)     │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ↓              ↓              ↓
      ┌──────────┐   ┌──────────┐   ┌──────────┐
      │ FastAPI  │   │ FastAPI  │   │ FastAPI  │
      │ Worker 1 │   │ Worker 2 │   │ Worker N │
      └────┬─────┘   └────┬─────┘   └────┬─────┘
           │              │              │
           └──────────────┼──────────────┘
                          │
                          ↓
                 ┌────────────────┐
                 │   ShaktiDB     │
                 │   (Primary)    │
                 └────────┬───────┘
                          │
                 ┌────────┴───────┐
                 │   ShaktiDB     │
                 │   (Replica)    │
                 └────────────────┘

            ┌────────────────────────┐
            │ Static Files Storage   │
            │ (CDN/Object Storage)   │
            └────────────────────────┘

            ┌────────────────────────┐
            │ Logging & Monitoring   │
            │ (ELK Stack / Grafana)  │
            └────────────────────────┘
```

## Technology Stack Visual

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────────────────┐   │
│  │ HTML5   │  │  CSS3   │  │  JavaScript (ES6+)  │   │
│  └─────────┘  └─────────┘  └─────────────────────┘   │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                    BACKEND                              │
│  ┌─────────┐  ┌───────────┐  ┌──────────────────┐    │
│  │ FastAPI │  │ Pydantic  │  │  SQLAlchemy      │    │
│  └─────────┘  └───────────┘  └──────────────────┘    │
│  ┌─────────┐  ┌───────────┐  ┌──────────────────┐    │
│  │ Uvicorn │  │  Loguru   │  │  Python 3.8+     │    │
│  └─────────┘  └───────────┘  └──────────────────┘    │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│              MACHINE LEARNING & ANALYSIS                │
│  ┌────────────┐  ┌──────────┐  ┌────────────────┐    │
│  │scikit-learn│  │ XGBoost  │  │  Androguard    │    │
│  └────────────┘  └──────────┘  └────────────────┘    │
│  ┌────────────┐  ┌──────────┐  ┌────────────────┐    │
│  │   pandas   │  │  numpy   │  │  imbalanced-   │    │
│  │            │  │          │  │     learn      │    │
│  └────────────┘  └──────────┘  └────────────────┘    │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                    DATABASE                             │
│  ┌────────────────────┐  ┌─────────────────────────┐  │
│  │  SQLite (Dev)      │  │  ShaktiDB (Production)  │  │
│  └────────────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

This architecture ensures:
- **Scalability**: Modular design, easy to scale
- **Maintainability**: Clear separation of concerns
- **Security**: Multiple layers of validation
- **Performance**: Efficient data flow
- **Extensibility**: Easy to add new features
