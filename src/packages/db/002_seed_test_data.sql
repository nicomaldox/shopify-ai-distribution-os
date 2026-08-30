-- src/packages/db/002_seed_test_data.sql

-- 1. Create a Creator (Alex)
INSERT INTO creators (creator_id, name, niche, commission_rate)
VALUES ('550e8400-e29b-41d4-a716-446655440000', 'Alex The Tech Bro', 'Tech & Software', 0.2000)
ON CONFLICT (creator_id) DO NOTHING;

-- 2. Create an Affiliate Link & Coupon for Alex
INSERT INTO affiliate_links (link_id, creator_id, slug, coupon_code)
VALUES ('110e8400-e29b-41d4-a716-446655440000', '550e8400-e29b-41d4-a716-446655440000', 'alex-tech', 'ALEX10')
ON CONFLICT (link_id) DO NOTHING;

-- 3. Mock Product
INSERT INTO products (product_id, title, price, image_url)
VALUES ('prod_999999999', 'Shopify AI Distribution OS Pro License', 3000.0000, 'https://placehold.co/400')
ON CONFLICT (product_id) DO NOTHING;

-- 4. Mock AI Generation Log (So the Analytics page isn't empty)
INSERT INTO ai_generation_logs (trace_id, creator_id, product_id, total_tokens, estimated_cost_usd, latency_ms, claims_accuracy_score, status)
VALUES ('trace_mock_001', '550e8400-e29b-41d4-a716-446655440000', 'prod_999999999', 1450, 0.0072, 1850, 1.0000, 'SUCCESS')
ON CONFLICT DO NOTHING;

-- 5. Mock Order and Ledger Entry (So the Earnings page isn't empty)
INSERT INTO orders (order_id, total_price, currency, financial_status, attributed_creator_id, attribution_source)
VALUES ('order_mock_001', 3000.0000, 'TWD', 'paid', '550e8400-e29b-41d4-a716-446655440000', 'COUPON')
ON CONFLICT (order_id) DO NOTHING;

INSERT INTO commission_ledger (creator_id, order_id, transaction_type, amount, status)
VALUES ('550e8400-e29b-41d4-a716-446655440000', 'order_mock_001', 'EARN', 600.0000, 'CLEARED');
