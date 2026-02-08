# Bear Application Department (BAD) - Operational Protocols

## 1. Sovereignty & Independence
*   **Self-Reliance**: BAD builds its own tools and maintains its own infrastructure. Specialization is good; dependency is bad.
*   **Contextual Awareness**: We may read, analyze, and learn from other projects/subprojects (e.g., `BearApp`, `vendor-open-bills`) to understand the ecosystem, but we **never edit them directly** unless they are explicitly transferred to our workspace.

## 2. Data Layering Strategy
*   **Read-Only Procurement**: We consume data from the broader organization (Google Sheets, Databases, files) as "Raw Material."
*   **Non-Interference**: We **do not manipulate, overwrite, or change** data that resides outside our department. We treat external data sources as immutable.
*   **The BAD Layer**: We maintain our own "Data Layer" (databases, JSON stores, separate spreadsheets) that sits *on top* of the organizational data. Use this layer for:
    *   Enrichment
    *   status tracking
    *   "Result" storage
    *   Analytics

## 4. Artifact Sovereignty (The "Golden Rule")
*   **BAD-Owned Only**: The Bear Application Department (BAD) and its agents are **strictly prohibited** from editing, deleting, moving, or modifying any artifact (file, code, spreadsheet, database) that was not explicitly created by BAD.
*   **Immutable External World**: All non-BAD artifacts are "Read-Only." We may index them, link to them, and read from them, but we never change them.
*   **Self-Contained State**: If BAD needs to track state about an external entity (e.g., "Result Link" for a Job), we must create our own parallel artifact (e.g., a BAD database or spreadsheet) to store that data.

## 5. Naming Conventions (The "Common Tongue")
*   **Standardization**: All resources (VMs, Databases, Bots, Keys) must follow the Global Naming Standard defined in [NAMING_STANDARDS.md](NAMING_STANDARDS.md).
*   **Format**: `[PROJECT]-[ENV]-[TYPE]-[NAME]` (e.g., `BAD-PROD-VM-FOUNDATION`).
*   **Enforcement**: The "Janitor" process is authorized to report any resource that deviates from this standard. Continuous deviations may result in automatic deprecation of the resource.
