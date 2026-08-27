-- src/packages/db/001_initial_schema.sql

-- Enable pgcrypto for UUID generation if needed (PostgreSQL 16 has gen_random_uuid() natively)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 1. Webhook Inbox (Idempotency)
CREATE TABLE IF NOT EXISTS webhook_inbox (
    webhook_id VARCHAR(255) PRIMARY KEY,
    topic VARCHAR(255) NOT NULL,
    shop_domain VARCHAR(255) NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Creators
CREATE TABLE IF NOT EXISTS creators (
    creator_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    niche VARCHAR(255),
    commission_rate NUMERIC(5,4) DEFAULT 0.2000, -- Default 20%
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS creator_profiles (
    profile_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID REFERENCES creators(creator_id) ON DELETE CASCADE,
    catchphrase TEXT,
    tone TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Affiliate Links & Promo Codes
CREATE TABLE IF NOT EXISTS affiliate_links (
    link_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID REFERENCES creators(creator_id) ON DELETE CASCADE,
    slug VARCHAR(255) UNIQUE NOT NULL,
    coupon_code VARCHAR(255) UNIQUE NOT NULL, -- e.g., ALEX10
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Click Events (Tracking Gateway)
CREATE TABLE IF NOT EXISTS click_events (
    click_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    link_id UUID REFERENCES affiliate_links(link_id) ON DELETE CASCADE,
    ip_hash VARCHAR(255) NOT NULL,
    user_agent TEXT,
    utm_source VARCHAR(255),
    utm_medium VARCHAR(255),
    utm_campaign VARCHAR(255),
    clicked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Products Catalog (Catalog Mirroring)
CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(255) PRIMARY KEY, -- Shopify Product ID
    title VARCHAR(255) NOT NULL,
    price NUMERIC(18,4),
    image_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. Orders & Order Items
CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR(255) PRIMARY KEY, -- Shopify Order ID
    total_price NUMERIC(18,4) NOT NULL,
    currency VARCHAR(10) DEFAULT 'TWD',
    financial_status VARCHAR(50),
    attributed_creator_id UUID REFERENCES creators(creator_id) ON DELETE SET NULL,
    attribution_source VARCHAR(50), -- 'COUPON', 'LINK', 'LAST_CLICK'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS order_items (
    item_id VARCHAR(255) PRIMARY KEY, -- Shopify Line Item ID
    order_id VARCHAR(255) REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id VARCHAR(255) NOT NULL,
    title VARCHAR(255),
    quantity INTEGER NOT NULL,
    price NUMERIC(18,4) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. Commission Ledger (Append-Only)
CREATE TABLE IF NOT EXISTS commission_ledger (
    ledger_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID REFERENCES creators(creator_id) ON DELETE CASCADE,
    order_id VARCHAR(255) REFERENCES orders(order_id) ON DELETE CASCADE,
    transaction_type VARCHAR(50) NOT NULL, -- 'EARN', 'REVERSAL', 'ADJUSTMENT'
    amount NUMERIC(18,4) NOT NULL,
    status VARCHAR(50) DEFAULT 'PENDING', -- 'PENDING', 'HELD', 'CLEARED'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Revoke destructive permissions on ledger for standard app users if running in prod
-- REVOKE UPDATE, DELETE ON commission_ledger FROM application_user;

-- 7. AI Generation Logs (Telemetry)
CREATE TABLE IF NOT EXISTS ai_generation_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trace_id VARCHAR(255),
    creator_id UUID REFERENCES creators(creator_id) ON DELETE SET NULL,
    product_id VARCHAR(255),
    total_tokens INTEGER,
    estimated_cost_usd NUMERIC(18,4),
    latency_ms INTEGER,
    claims_accuracy_score NUMERIC(5,4), -- 0.0 to 1.0
    status VARCHAR(50), -- 'SUCCESS', 'HALTED', 'REJECTED'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
