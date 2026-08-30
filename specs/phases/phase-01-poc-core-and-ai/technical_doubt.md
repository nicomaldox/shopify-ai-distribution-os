# Technical Doubt: Functions 2 & 3 (Shopify Webhook Attribution)

## Current Status
Currently, **Function 2** (Sales EARN attribution) and **Function 3** (Refund REVERSAL attribution) are not executing properly on the live server. 

When you place a dummy order or issue a refund on Shopify, Shopify successfully transmits the webhook to our Cloudflare Tunnel URL (`/webhooks/shopify/`). However, the Core API instantly rejects the payload with a **`401 Unauthorized`** error and drops the transaction.

## Root Cause Analysis
The rejection is happening inside our `verify_shopify_webhook` middleware (`src/apps/core-api/dependencies/security.py`).

1. **HMAC Signature Mismatch:** Shopify signs every webhook with an HMAC-SHA256 signature using a shared secret. Our API calculates the signature on the incoming body using the `SHOPIFY_WEBHOOK_SECRET` loaded in our `.env` file and compares them. If they don't match, we assume the webhook was forged by an attacker and block it.
2. **The Secret is Incorrect:** In your `.env` file, the `SHOPIFY_WEBHOOK_SECRET` is set to `shpss_b06c...`. This is your Shopify Custom App API Secret. 
3. **The Shopify Quirk:** When you manually create webhooks in the Shopify Admin UI (*Settings > Notifications*), Shopify **does not use the Custom App API Secret** to sign them. Instead, it uses a unique Notification Webhook Secret. 

Because the API is using the Custom App Secret to verify a payload that was signed with the Notification Secret, the cryptographic signatures do not match, causing the `401 Unauthorized` block.

## How to Resolve

We have two ways to resolve this doubt and fix Functions 2 & 3:

### Option A: Use the Correct Notification Secret (Easiest)
1. Go to your Shopify Admin Panel > **Settings > Notifications**.
2. Scroll to the very bottom of the page to the **Webhooks** section.
3. Look for the text that says: *"All your webhooks will be signed with..."*
4. Copy that specific string (it is usually shorter than the `shpss_` API secret).
5. Paste it into your local `.env` file as `SHOPIFY_WEBHOOK_SECRET=your_new_secret`.
6. Tell me to re-deploy the `.env` to the VPS.

### Option B: Create the Webhooks via GraphQL/API
Instead of creating the webhooks manually in the Shopify UI, I can write a quick script that uses your Custom App API credentials to register the webhooks programmatically. If we register them via the API, Shopify *will* sign them using the `shpss_` secret you already provided, and everything will magically work without changing the `.env`.

**Please review this document and let me know if you would like to proceed with Option A or Option B.**
