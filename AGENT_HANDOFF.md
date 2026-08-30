# Agent Handoff Context (AI Distribution OS)

> **To the Next Agent:** Read this document carefully before taking any action. It contains the exact current state of the project, architecture, credentials, and known blockers. Do not start from zero.

## 1. Project Overview
**Name:** AI KOL Distribution OS
**Description:** A Shopify-integrated platform that attributes sales to AI Creators and automatically generates UGC video scripts for new products.
**Stack:**
- **Backend:** Python (FastAPI), SQLAlchemy (Async), PostgreSQL, Redis (Valkey).
- **Frontend:** React (Next.js/Vite for Admin/Creator web apps).
- **Infrastructure:** Ubuntu VPS, Docker Compose, NGINX (Reverse Proxy), Cloudflare Tunnels (Temporary Webhook testing).
- **Automation:** n8n (for AI Video Factory workflows).

## 2. Infrastructure & Credentials
- **VPS IP:** `181.215.135.249`
- **SSH Login:** `root` / `Quiero,1pitoni`
- **Deployment Path (VPS):** `/root/shopify-ai-distribution-os`
- **Current Connectivity:** 
  - NGINX is installed and routing traffic to Docker containers (ports 8080, 3000, 3001). 
  - Let's Encrypt SSL failed previously because DNS is not pointing to the VPS (user's domain `nicomaldo.es` points to a different IPv6 server).
  - **Workaround in use:** We are using a temporary Cloudflare Tunnel (`https://old-shed-suse-translate.trycloudflare.com`) to bypass Shopify's HTTPS requirement for testing webhooks.

## 3. Current State & Completed Work
- **Phase 1 is complete:** The core API, database schema, and frontend dashboards are fully built and deployed to the VPS via Docker.
- **n8n Workflow:** The AI script generation workflow is fully operational. The payload schema for `POST /ai/generate-script` requires `product_id` and `creator_id` (not title/price).

## 4. Current Blocker / Paused Work (The Technical Doubt)
The user was testing **Function 2 (Sales EARN Attribution)** and **Function 3 (Refund REVERSAL Attribution)**. 
- **The Issue:** Shopify webhooks (`orders/paid` and `refunds/create`) are hitting the API correctly, but the API instantly rejects them with a `401 Unauthorized` (Invalid HMAC signature).
- **What we tried:** We realized manual webhooks use a different "Notification Secret" (`348a6b...`) instead of the App API Secret. We successfully updated the `.env` on the VPS with this correct secret and restarted the API.
- **The Result:** It still throws a `401 Unauthorized`.
- **Root Cause Hypothesis:** The Cloudflare Tunnel might be slightly mutating the raw JSON bytes (compression, whitespace formatting) before it hits FastAPI, OR FastAPI's `await request.body()` is parsing the bytes differently than Shopify hashed them. HMAC requires a 1:1 bit-perfect match.
- **Status:** The user explicitly requested to PAUSE investigation on this webhook issue and move on to something else. Do NOT attempt to fix the webhooks unless the user explicitly asks you to resume it.

## 5. Next Steps for You
1. Acknowledge this context.
2. Ask the user what new feature or component they would like to work on next, since the webhook debugging is officially paused.
3. Follow the strict SDD (Spec-Driven Development) rules outlined in `AGENTS.md` for any new code.
