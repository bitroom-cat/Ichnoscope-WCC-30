Here is the architecture. Solid lines are the 15-hour minimum demo, and dashed lines are the post-demo extras.

```mermaid
flowchart TD
    %% ===== Sources =====
    SENTRY["Sentry error event"]
    FIX["fixtures/*.json<br/>saved Sentry payloads"]

    %% ===== Entry =====
    subgraph ENTRY["Entry points"]
        REPLAY["replay.py<br/>(demo / tests, --dry-run)"]
        GATE["FastAPI gateway<br/>verify HMAC, reply 200"]
    end

    %% ===== Core pipeline =====
    subgraph CORE["Ichnoscope core pipeline (plain Python functions)"]
        DEDUPE[("SQLite dedupe<br/>fingerprint, count")]
        PARSE["parse.py<br/>Sentry JSON to Incident<br/>last in_app frame, path strip"]
        BLAME["blame.py<br/>GraphQL blame at release SHA<br/>to Culprit + diff"]
        DECIDE{"Blame<br/>conclusive?"}
        FALLBACK["Fallback: 3 latest commits<br/>on file, low-confidence"]
        EXPLAIN["explain.py<br/>one LLM call to Explanation<br/>domain, hypothesis, 3 checks"]
        TEMPLATE["No-LLM template<br/>stack + diff only"]
        SEV["severity.py<br/>rule-based P1/P2/P3"]
        DISPATCH["dispatch.py<br/>build issue, labels, suggested owner"]
    end

    %% ===== LLM chain =====
    subgraph LLM["LLM fallback methods"]
        L1["Gemini Flash (tool caaling)"]
        L2["Groq"]
        L3["OpenRouter :free"]
        L4["pollination api () "]
        L1 -->|"429 / 5xx / bad JSON or  <br/> use for the descriptive overview"| L2
        L2 -->|"fail"| L3
        L3 -->|"use for simple tasks "| L4
    end

    %% ===== External systems =====
    subgraph EXT["External systems"]
        GH_GQL["GitHub GraphQL<br/>blame + PR"]
        GH_REST["GitHub REST<br/>commit diff, create issue"]
        SLACK["Slack webhook"]
    end

    OUT["GitHub Issue<br/>diff, hypothesis, checklist,<br/>suggested owner, labels"]

    %% ===== MVP flow (solid) =====
    FIX --> REPLAY
    REPLAY --> PARSE
    PARSE --> BLAME
    BLAME <--> GH_GQL
    BLAME <--> GH_REST
    BLAME --> DECIDE
    DECIDE -->|"yes, high"| EXPLAIN
    DECIDE -->|"no"| FALLBACK
    FALLBACK --> EXPLAIN
    EXPLAIN <--> L1
    EXPLAIN -->|"all providers fail"| TEMPLATE
    EXPLAIN --> DISPATCH
    TEMPLATE --> DISPATCH
    DISPATCH --> GH_REST
    GH_REST --> OUT

    %% ===== Post-demo flow (dashed) =====
    SENTRY -.-> GATE
    GATE -.-> DEDUPE
    DEDUPE -.->|"new / regression"| PARSE
    DEDUPE -.->|"repeat: bump + comment"| GH_REST
    SEV -.-> DISPATCH
    EXPLAIN -.-> SEV
    DISPATCH -.-> SLACK

    %% ===== Styling =====
    classDef det fill:#E6F1FB,stroke:#185FA5,color:#0C447C;
    classDef llm fill:#EEEDFE,stroke:#534AB7,color:#3C3489;
    classDef ext fill:#F1EFE8,stroke:#5F5E5A,color:#2C2C2A;
    classDef out fill:#E1F5EE,stroke:#0F6E56,color:#085041;
    class PARSE,BLAME,DECIDE,FALLBACK,SEV,DISPATCH,DEDUPE,REPLAY,GATE,TEMPLATE det;
    class EXPLAIN,L1,L2,L3,L4 llm;
    class GH_GQL,GH_REST,SLACK,SENTRY,FIX ext;
    class OUT out;
```

Blue boxes are deterministic code, purple boxes are the LLM, grey boxes are external systems and green is the final output. Only the purple boxes involve a model, which is the "code gathers evidence, LLM explains" rule.
