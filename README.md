# Transaction Intelligence Platform

> A pluggable platform that runs **five independent fintech analyzers** over the same payment data and surfaces everything they find in one unified review queue. One backbone, five swappable brains, one contract.

| # | Analyzer | Detects / does | Technique | Metric |
|---|---|---|---|---|
| 1 | **AML** | fraud + laundering (structuring, velocity, geo, large-amount) | rules + baselines + ML ensemble + LLM explain | PR-AUC / Recall |
| 2 | **Reconciliation** | breaks between ledger and processor | fuzzy matching + discrepancy typing + LLM | Precision / Recall |
| 3 | **Categorization** | merchant category / purpose code | normalize → lookup → TF-IDF + NB | Macro-F1 |
| 4 | **Disputes** | chargeback lifecycle + deadlines + rebuttals | reason-code FSM + LLM draft | Win rate |
| 5 | **Reporting** | SAR narratives from other analyzers' findings | grounded LLM + faithfulness check | Grounding |

---

## 1. System architecture

The whole platform on one screen — sources flow into the backbone, the backbone runs the five analyzers, every analyzer writes into one unified `Finding` store, and the API + dashboard surface it.

```mermaid
flowchart TB
    subgraph SRC["DATA SOURCES"]
        direction LR
        TX["Transactions"]
        LP["Ledger + Processor"]
        DP["Disputes"]
    end

    subgraph CORE["CORE — platform backbone"]
        direction TB
        ING["Ingestion (loader + adapters)"]
        REG["Analyzer Registry"]
        PIPE["Pipeline Runner"]
        LLM["Groq LLM (explain / draft / check ONLY)"]
        DB[("Store: Transactions / Findings / AuditLog")]
    end

    subgraph AN["FIVE PLUGGABLE ANALYZERS"]
        direction LR
        AML["1 AML"]
        RC["2 Reconciliation"]
        CT["3 Categorization"]
        DS["4 Disputes"]
        RP["5 Reporting"]
    end

    subgraph OUT["SURFACING"]
        direction LR
        API["FastAPI: /findings /stats /graph"]
        UI["Next.js Dashboard + Network Graph"]
    end

    TX --> ING
    LP --> ING
    DP --> ING
    ING --> DB
    DB --> PIPE
    REG --> PIPE
    PIPE --> AML
    PIPE --> RC
    PIPE --> CT
    PIPE --> DS
    PIPE --> RP
    AML --> DB
    RC --> DB
    CT --> DB
    DS --> DB
    RP --> DB
    AML -.-> LLM
    DS -.-> LLM
    RP -.-> LLM
    RP -. reads findings .-> DB
    DB --> API
    API --> UI

    classDef src fill:#EAF2F8,stroke:#3E7CA8,color:#15213B
    classDef core fill:#E8EEF7,stroke:#27406B,color:#15213B
    classDef anlz fill:#27406B,stroke:#15213B,color:#ffffff
    classDef out fill:#E7F4EF,stroke:#2E8B6F,color:#15213B
    class TX,LP,DP src
    class ING,REG,PIPE,LLM,DB core
    class AML,RC,CT,DS,RP anlz
    class API,UI out
```

---

## 2. The contract that makes it pluggable

Every analyzer implements **one interface**. That is the entire architecture — add a sixth analyzer by dropping in a class, not by rewiring the system.

```mermaid
classDiagram
    class Analyzer {
        <<interface>>
        +str name
        +required_inputs() list~str~
        +run(session, config) RunResult
        +evaluate(session) str
    }
    class AMLAnalyzer
    class ReconciliationAnalyzer
    class CategorizationAnalyzer
    class DisputeAnalyzer
    class ReportingAnalyzer

    Analyzer <|.. AMLAnalyzer
    Analyzer <|.. ReconciliationAnalyzer
    Analyzer <|.. CategorizationAnalyzer
    Analyzer <|.. DisputeAnalyzer
    Analyzer <|.. ReportingAnalyzer

    class RunResult {
        +int findings_created
        +str message
    }
    class Finding {
        +str id
        +str analyzer
        +str entity_id
        +str finding_type
        +Decimal score
        +str band
        +str status
        +str summary
        +str explanation
        +dict payload_json
    }
    AMLAnalyzer ..> Finding : emits
    ReconciliationAnalyzer ..> Finding : emits
    CategorizationAnalyzer ..> Finding : emits
    DisputeAnalyzer ..> Finding : emits
    ReportingAnalyzer ..> Finding : emits
```

---

## 3. Traceability — how any of the five is tracked

Every analyzer writes into the **same `Finding` table**, so a flagged transaction, a reconciliation break, a low-confidence category, a dispute deadline, and a drafted SAR all land in one queue — each traceable back to the evidence that produced it.

```mermaid
flowchart LR
    IN["Raw input<br/>(txn / ledger pair / dispute)"] --> A["Analyzer.run()"]
    A --> EV["Evidence assembled<br/>(rules / scores / records)"]
    EV --> F["FINDING written<br/>analyzer + entity_id + type + score + band"]
    F --> Q["Unified review queue<br/>filter by analyzer / severity / status"]
    Q --> H["Human review"]
    H --> RES["Resolved / actioned"]
    F -.-> API["/findings/{id} -> full evidence trail"]
```

A finding moves through an explicit status lifecycle:

```mermaid
stateDiagram-v2
    [*] --> open: analyzer emits
    open --> needs_review: low confidence / threshold
    open --> pending_review: LLM-drafted artifact (SAR / rebuttal)
    needs_review --> resolved: analyst actions
    pending_review --> resolved: human signs off
    resolved --> [*]
    note right of pending_review
        LLM never auto-resolves
        or files — human required
    end note
```

---

## 4. Data model

The shared `Finding` is the spine; each analyzer keeps its own domain tables for detail.

```mermaid
erDiagram
    TRANSACTIONS ||--o{ FINDINGS : "entity_id"
    ANALYZER_RUNS ||--o{ FINDINGS : "run_id"
    TRANSACTIONS ||--o| ACCOUNT_BASELINES : "account_id"
    LEDGER_ENTRIES ||--o{ DISCREPANCIES : "produces"
    DISPUTES ||--o{ FINDINGS : "entity_id"
    FINDINGS ||--o{ REPORTS : "feeds SAR"

    TRANSACTIONS {
        string transaction_id PK
        string account_id
        string counterparty_account
        decimal amount
        string merchant
        string country
        datetime timestamp
    }
    FINDINGS {
        string id PK
        string analyzer
        int run_id FK
        string entity_type
        string entity_id
        string finding_type
        decimal score
        string band
        string status
        string summary
        string explanation
        json payload_json
    }
    ANALYZER_RUNS {
        int id PK
        string analyzer_name
        datetime started_at
    }
    ACCOUNT_BASELINES {
        string account_id PK
        decimal amount_median
        decimal amount_mad
        json seen_countries
    }
    LEDGER_ENTRIES {
        string id PK
        string source
        string external_ref
        decimal amount
        string status
    }
    DISCREPANCIES {
        string id PK
        string type
        decimal amount_diff
    }
    DISPUTES {
        string dispute_id PK
        string transaction_id
        string reason_code
        string status
        datetime deadline
    }
    REPORTS {
        string report_id PK
        string entity_id
        string status
    }
```

---

## 5. The five analyzers — one pipeline each

Same contract, five completely different brains. Each gets equal depth below.

### 1 — AML  ·  *rules + baselines + ensemble ML + LLM*

```mermaid
flowchart LR
    T["Transaction"] --> R["Rule Engine<br/>velocity / structuring / geo / large-amount"]
    T --> B["Behavioral Baseline<br/>per-account median + MAD"]
    T --> FE["Feature Builder<br/>+ graph features (fan-in/out)"]
    B --> FE
    FE --> EN["ML Ensemble<br/>Isolation Forest + LightGBM"]
    R --> SC["Risk Scorer<br/>weighted 0-100"]
    EN --> SC
    SC --> BD["Severity Band"]
    BD --> F["FINDING"]
    F --> X["LLM Explanation<br/>plain-English + suggested action"]
```

### 2 — Reconciliation  ·  *matching + discrepancy typing + LLM*

```mermaid
flowchart LR
    L["Internal Ledger"] --> N["Normalize refs<br/>+ date tolerance"]
    P["Processor"] --> N
    N --> M{"Match?"}
    M -->|exact / fuzzy| OK["Matched"]
    M -->|no match| D["Classify discrepancy"]
    D --> D1["missing_internal / missing_processor"]
    D --> D2["amount_mismatch"]
    D --> D3["duplicate_processor"]
    D --> D4["status_mismatch"]
    D1 --> F["FINDING"]
    D2 --> F
    D3 --> F
    D4 --> F
    F --> X["LLM: explains the likely cause of the break"]
```

### 3 — Categorization  ·  *normalize → lookup → ML*

```mermaid
flowchart LR
    M["Messy merchant string<br/>'PAYPAL *AMZN MKTP #445'"] --> NZ["Normalize<br/>strip prefixes/suffixes/punct"]
    NZ --> L{"In lookup table?"}
    L -->|yes| C1["Category (conf 1.0)"]
    L -->|no| ML["TF-IDF + Naive Bayes"]
    ML --> CF{"Confidence high?"}
    CF -->|yes| C2["Category"]
    CF -->|low| NR["FINDING: needs_review"]
```

### 4 — Disputes  ·  *reason-code FSM + deadlines + LLM rebuttal*

```mermaid
flowchart LR
    DP["Dispute"] --> RC["Reason code -> required evidence map"]
    RC --> DL{"Deadline approaching?"}
    DL -->|yes| URG["FINDING: urgent_deadline"]
    RC --> RB["LLM drafts rebuttal<br/>(legal-brief tone, evidence-matched)"]
    RB --> PR["FINDING: pending_review"]
    DP --> ST["State: open -> submitted -> won/lost"]
    ST --> WR["Win-rate metric"]
```

State machine:

```mermaid
stateDiagram-v2
    [*] --> open
    open --> evidence_gathering: reason-code evidence assembled
    evidence_gathering --> submitted: rebuttal drafted + filed (human)
    submitted --> won
    submitted --> lost
    won --> [*]
    lost --> [*]
```

### 5 — Reporting  ·  *grounded SAR + faithfulness check (the capstone)*

```mermaid
flowchart LR
    FND["Other analyzers' FINDINGS<br/>(AML especially)"] --> EV["Assemble evidence (JSON)"]
    EV --> GEN["LLM drafts SAR<br/>'use ONLY this evidence'"]
    GEN --> CHK["Faithfulness check<br/>'anything NOT in evidence?'"]
    CHK -->|clean| OK["FINDING: pending_review"]
    CHK -->|hallucination| FLAG["FINDING: pending_review + failed_grounding"]
    OK --> HUM["Human signs off -> file"]
    FLAG --> HUM
```

---

## 6. Deployment topology

Frontend on Vercel; the Python/ML backend on a container host with Postgres. (Vercel cannot host the stateful FastAPI + ML backend — see `DEPLOYMENT.md`.)

```mermaid
flowchart LR
    U["Browser"] --> V["VERCEL<br/>Next.js dashboard"]
    V -->|"NEXT_PUBLIC_API_URL + CORS"| B["CONTAINER HOST<br/>FastAPI + analyzers + ML"]
    B --> PG[("Managed Postgres")]
    B -.->|"explain / draft / check"| G["Groq API"]
    GH["GitHub Actions CI<br/>pytest on every PR"] -.-> B

    classDef fe fill:#E8EEF7,stroke:#27406B,color:#15213B
    classDef be fill:#27406B,stroke:#15213B,color:#ffffff
    classDef ext fill:#FAF5E6,stroke:#C29A2E,color:#15213B
    class V fe
    class B be
    class PG,G,GH ext
```

---

## 7. Runtime — opening a flagged item

```mermaid
sequenceDiagram
    actor Analyst
    participant UI as Dashboard
    participant API as FastAPI
    participant DB as Store
    Analyst->>UI: open review queue
    UI->>API: GET /findings?band=critical
    API->>DB: query findings
    DB-->>API: findings
    API-->>UI: JSON
    Analyst->>UI: click a finding
    UI->>API: GET /findings/{id}
    API->>DB: finding + evidence + explanation
    DB-->>API: detail
    API-->>UI: full evidence trail
    UI-->>Analyst: render (score, rules, LLM explanation)
```

---

## Quickstart

```bash
uv sync
uv run python -m interface.cli generate --accounts 50 --days 30 --out data.csv
uv run python -m interface.cli ingest data.csv
uv run python -m interface.cli run aml            # aml | reconciliation | categorization | disputes | reporting
uv run python -m interface.cli train --labels data.csv
uv run python -m interface.cli evaluate           # regenerate the combined SCORECARD.md
uv run uvicorn interface.api:app --reload         # API
cd frontend && npm install && npm run dev         # dashboard (set NEXT_PUBLIC_API_URL)
```

## Scorecard (per analyzer, the right metric for each)

| Analyzer | Headline (synthetic data; regenerate via `evaluate`) |
|---|---|
| AML | ensemble lift ~+9.6pts recall over rules (~50.0% -> ~59.6%), F1 ~0.702 |
| Reconciliation | ~84.4% recall at 100% precision on injected breaks |
| Categorization | macro-F1 ~0.51 (lightweight TF-IDF + NB) |
| Disputes | workflow metrics — 42.9% win rate, 37 open |
| Reporting | grounded SAR drafts with a faithfulness check (needs a Groq key) |

*Keep this in sync with `SCORECARD.md` — both come from one `evaluate` run.*

## Docs

`spec.md` (technical spec) · `AGENTS.md` (contributor + agent guide) · `CLAUDE.md` (Claude quick ref) · `DEPLOYMENT.md` (Vercel + backend) · `Roadmap.md` (phase history)
