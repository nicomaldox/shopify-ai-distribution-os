# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2026-09-03

### Added
- **Open Redirect Defense Verification, Privacy Auditing & Test Hardening**
  - Corrected the privacy compliance SQL verification query in `USER_GUIDE.md` to explicitly `INNER JOIN` `affiliate_links` on `link_id` and query `clicked_at`, resolving `ERROR: column "slug" does not exist`.
  - Added comprehensive verification guidelines in `USER_GUIDE.md` detailing browser and `curl.exe` methods for verifying Open Redirect Defense (`HTTP 400 Bad Request` on unapproved slugs, unauthorized `dest` URLs, and SSRF private IP attempts).
  - Extended `tests/test_security_defenses.py` with 4 automated test cases (`test_redirect_gateway_unapproved_slug`, `test_redirect_gateway_unauthorized_dest_param`, `test_redirect_gateway_ssrf_dest_param`, `test_redirect_gateway_approved_slug_success`), bringing the test suite to 29 passing tests (100% pass rate).
- **Frontend Data Ergonomics, Cross-Origin Sync & Database Hygiene**
  - Added `CORSMiddleware` to `src/apps/core-api/main.py` allowing cross-origin requests from `http://localhost:3000` (Creator Studio) and `http://localhost:3001` (Admin Console).
  - Built `SyncButton.tsx` for Creator Studio (`src/apps/creator-web/src/components/SyncButton.tsx`) to allow creators to trigger instant order reconciliation from their Earnings dashboard.
  - Resolved commission vs order value ambiguity: updated Creator and Admin UI tables to display both Net Order Value (`order_total`) and Commission Earned (20%) side-by-side.
  - Implemented local timezone conversion (`Asia/Taipei`) in `frontend_api.py` via PostgreSQL `AT TIME ZONE :tz` and ISO-8601 formatting, replacing raw server UTC timestamps with local clock time.
  - Safely purged mock/simulated transactions (`order_mock_001` and empty test order `123`) and executed full clean database reset across `commission_ledger`, `orders`, and `order_items`.
  - Added `SHOPIFY_SYNC_SINCE_ID` configuration to `shopify_sync.py` to establish an order baseline, preventing the 30-second background daemon from re-syncing legacy Shopify store test orders after a clean database wipe.
  - Permanently pinned frontend ports in `package.json` (`next dev -p 3000` for Creator Studio, `next dev -p 3001` for Admin Console) and eliminated Next.js 16 metadata wrapper hydration errors.
- **Resilient Hybrid Ingestion Engine & Local Environment Transition**
  - Implemented `shopify_sync.py` to pull paid orders and refunds directly from Shopify Admin REST API, removing single-point-of-failure reliance on public tunnels and webhook HMAC matching.
  - Added background polling scheduler (`scheduler.py`) running every 30 seconds for automated order reconciliation via FastAPI lifespan.
  - Added manual `POST /webhooks/shopify/sync` endpoint and wired "↻ Sync Shopify Orders" trigger button in the Admin Console.
  - Hardened `verify_shopify_webhook` middleware with automatic `.strip()` of CRLF artifacts, multi-secret candidate fallback (Notification Secret + Custom App Secret), and development diagnostic logging.
  - Configured local Docker Desktop development stack for PostgreSQL 16 and Valkey 8 (`docker compose up -d postgres valkey`).
  - Successfully verified live end-to-end sync against store `0efjx4-fp.myshopify.com`: ingested 11 real Shopify orders and recorded immutable commission accruals into PostgreSQL `commission_ledger`.
  - Integrated `load_dotenv()` into `main.py` entrypoint for reliable local configuration loading across reload cycles.
  - Added automated test suites: `tests/test_financial_scenarios.py` (5 financial accounting scenarios) and `tests/test_shopify_sync.py` (pull-sync order ingestion and idempotency), achieving 100% test pass rate (25/25 tests passing).
  - Verified concurrent local operation of full stack: PostgreSQL 16 (5432), Valkey 8 (6379), Core API (8000), Admin Console (3001), and Creator Studio (3000).
- **Day 8: VPS Deployment & Live Demo**
  - Added PostgreSQL `002_seed_test_data.sql` to populate mock creators, affiliates, and AI telemetry for demo purposes.
  - Created `demo_script.md` for live stakeholder presentation.
  - Verified `docker-compose.yml` configuration for seamless `docker compose up -d` single-command deployment on Production VPS.
  - Remediated database connection URL for production Docker deployment and finalized Phase 1 live deployment.
- **Day 6: Cloud AI Video & Audio Rendering Factory**
  - Integrated Fal.ai / Wan2.2 API for 9:16 vertical video generation.
  - Integrated OpenAI TTS for synchronized voiceover.
  - Built `media_assembler.py` using FFmpeg with `drawtext` filter for text overlay hooks.
- **Day 7: Creator Studio UI & Admin Console**
  - Scaffolded Next.js App Router applications with Vanilla CSS glassmorphism.
  - Built live Earnings and Audit Ledger views powered by real-time PostgreSQL data.
  - Created frontend API routers to fetch Postgres data directly to React Server Components.
  - Exported n8n workflows orchestrating Webhook -> AI Director -> Video Factory.
- **Day 7 Audit Remediation**
  - Hardened PostgreSQL `commission_ledger` with `ON DELETE RESTRICT` cascade protection.
  - Wired frontends directly to backend APIs, replacing static mock data with real-time API integrations.
- **Day 2: Webhook Security & Idempotency**
  - Implemented constant-time HMAC-SHA256 Shopify webhook verification (`security.py`).
  - Added PostgreSQL `webhook_inbox` for deduplication and replay attack prevention (`webhooks.py`).
- **Day 3: Redirect Gateway & Attribution Engine**
  - Built high-performance `/r/{slug}` redirect route with GDPR-compliant IP hashing (`tracking.py`).
  - Built Multi-Evidence Attribution Resolver (Priority: Coupon Code > Signed Token > Last Eligible Click).
- **Day 4: Append-Only Commission Ledger & Reversals**
  - Built immutable financial ledger (`ledger.py`) using strictly `Decimal` math with `ROUND_HALF_UP` precision.
  - Implemented dynamic proportional math for full/partial refund reversals.
  - Wired `orders/paid` and `refunds/create` webhooks to atomic ledger transactions.
- **Day 5: AI Director Agent (LangChain)**
  - Integrated LangChain `create_agent` with OpenAI GPT-4o and Pydantic `DirectorSpec` structured output.
  - Built `@after_model` claims validator (LLM Judge) to ensure ad disclosures and marketing compliance.
  - Built `@after_agent` telemetry logger to capture token usage, latency, and cost into `ai_generation_logs`.
  - Exposed synchronous `POST /ai/generate-script` endpoint for n8n orchestration.
- **Audit Remediation & Test Suite**
  - Fixed Day 4 financial precision pipeline: `webhooks.py` now parses refund transactions using precise `Decimal` logic instead of `float()`.
  - Fixed Day 4 atomicity gaps: Webhooks now commit orders and ledger entries in a single transaction block.
  - Added Test Scenario 5 to `test_refund_reversals.py` to cryptographically prove negative running balances are handled correctly.
  - **Day 5 Audit Fixes**: Completely refactored AI Director to align with production LangGraph APIs.
  - Replaced speculative API calls with a proper LangGraph `StateGraph`.
  - Upgraded keyword-based validator to a secondary LLM Judge node for strict compliance.
  - Resolved circular imports by extracting `DirectorSpec` into `schemas.py`.
  - Configured LangSmith tracing environment variables.
  - Created `pytest` suite for security, deduplication, attribution logic, and AI Director schema/telemetry (`tests/`).
  - Hardened redirect gateway with strict Shopify domain allowlist and SSRF private IP blocking.
  - Implemented cryptographically signed HMAC referral tokens (`?ref=slug.signature`) to prevent attribution spoofing.
  - Added `products` catalog mirroring table to PostgreSQL schema.

## [Unreleased] - 2026-08-26
### Added
- Initialized Spec-Driven Development (SDD) repository architecture (`specs/constitution/`, `specs/phases/`).
- Created Project Constitution: `mission.md`, `tech-stack.md`, and `roadmap.md`.
- Created Phase 1 PoC sub-specifications: `requirements.md`, `plan.md`, and `validation.md`.
- Created Executive Timeline and Daily Tasks Report (`report.md`).
- Defined coding rules and financial ledger constraints in `AGENTS.md`.
- Added LLM Observability & Telemetry architecture (LangSmith + `ai_generation_logs` in PostgreSQL).
- Added step-by-step Shopify Custom App creation checklist in `specs/phases/phase-01-poc-core-and-ai/plan.md`.

### Configured
- Confirmed Shopify Development Store sandbox strategy.
- Selected OpenAI GPT-4o for AI Director scriptwriting and OpenAI TTS for voiceover narration.
- Integrated LangChain v1.x+ (`create_agent`) with Pydantic `DirectorSpec` structured output and Claims Middleware.
- Selected Cloud Video Generation API (Fal.ai / Replicate Wan2.2, pay-per-second, ~$0.03/video) for zero-local-GPU execution.
- Connected with user's pre-existing self-hosted n8n instance on Production VPS for event dispatching.
- Set default creator commission to 20% (dynamically configurable) with NTD (TWD) currency and English locale.
- Configured Cloudflare Tunnel for local development and Docker Compose for Production VPS production deployment.
