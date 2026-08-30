# 🚀 Live Demo Presentation Script
## Shopify AI Distribution OS - Phase 1 PoC

*Follow this script to demonstrate the end-to-end functionality of the platform to stakeholders.*

---

## 🛑 Pre-flight Check
1. Ensure the VPS deployment is active: `docker ps` shows 5 running containers (core-api, postgres, valkey, creator-web, admin-web).
2. Ensure you have your Shopify Development store open in a tab.
3. Open the **Creator Studio** (`http://nicomaldo.es:3000`) in Tab 1.
4. Open the **Admin Console** (`http://nicomaldo.es:3001`) in Tab 2.
5. Open the **FastAPI Swagger UI** (`http://nicomaldo.es:8000/docs`) in Tab 3.

---

## 🎬 Act 1: The Creator Studio & AI Generation
**"Welcome to the Creator Studio. This is where influencers log in to get their daily tasks, AI-generated assets, and track their earnings."**
1. Show the **Creator Studio -> Assets & Links**. Point out the Tracking Link (`ALEX10` coupon).
2. Go to the **FastAPI Swagger UI** (`/ai/generate-script`).
3. Click **Try it out**.
4. Enter `product_title: Shopify AI Distribution OS Pro`, `product_price: 3000`, `product_id: prod_999999999`.
5. Execute the request.
6. Show the response. **"The LangGraph AI Director just parsed the product, validated it against our compliance LLM Judge (injecting mandatory #Ad disclosures), and triggered the FFmpeg Video Factory."**
7. Go to **Admin Console -> AI Telemetry**. Point out the newly inserted log showing tokens spent and claims accuracy.

---

## 🎬 Act 2: The Shopify Purchase & Real-Time Attribution
**"Now, let's simulate a customer buying the product using Alex's coupon code."**
1. Go to your **Shopify Storefront**. Add a product to the cart that totals $3,000.
2. Go to checkout. **CRITICAL STEP:** Enter the discount code `ALEX10`.
3. Complete the checkout using the Bogus Payment Gateway.
4. **"Shopify has just fired a secure HMAC webhook to our Core API."**
5. Immediately switch to the **Creator Studio -> Earnings** tab and refresh.
6. **"Boom! The Creator's balance instantly increased by +NT$600 (20% commission). This is an immutable double-entry ledger."**

---

## 🎬 Act 3: The Refund Reversal
**"What happens if a customer refunds? We don't want to pay commission on returned items, but we also can't delete database rows because this is a financial ledger."**
1. Go to the **Shopify Admin Panel** -> Orders.
2. Select the order you just made. Click **Refund**.
3. Refund exactly half the order (e.g., $1,500).
4. **"Shopify fires a `refunds/create` webhook. Let's look at the Creator Studio again."**
5. Refresh the **Creator Studio -> Earnings** tab.
6. **"The system dynamically calculated a proportional reversal. You'll see a new REVERSAL entry for -$300, and the pending balance has dropped accordingly. No rows were deleted or updated; it's completely append-only."**

---

## 🎬 Act 4: The Admin Audit
**"Finally, let's look at the Admin view."**
1. Switch to the **Admin Console -> Live Ledger**.
2. **"Here is the raw PostgreSQL view. You can see the exact UUIDs, the `EARN` and `REVERSAL` transaction types, and timestamps. This is the bulletproof source of truth."**

---
**🎉 End of Demo! 🎉**
