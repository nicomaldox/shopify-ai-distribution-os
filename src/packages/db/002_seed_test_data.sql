-- src/packages/db/002_seed_test_data.sql

-- 1. Create Beauty & Skincare Creators
INSERT INTO creators (creator_id, name, niche, commission_rate)
VALUES 
('550e8400-e29b-41d4-a716-446655440001', 'Elena Lin (美妝護膚 艾琳娜)', 'Skincare & Clean Beauty', 0.2000),
('550e8400-e29b-41d4-a716-446655440002', 'Chloe Chen (護膚日記 克洛伊)', 'Sensitive Skin Care', 0.2000)
ON CONFLICT (creator_id) DO NOTHING;

-- 2. Create Affiliate Links & Coupons
INSERT INTO affiliate_links (link_id, creator_id, slug, coupon_code)
VALUES 
('110e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 'elena-glow', 'ELENA10'),
('110e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440002', 'chloe-skin', 'CHLOE20')
ON CONFLICT (link_id) DO NOTHING;

-- 3. Beauty & Skincare Products
INSERT INTO products (product_id, title, price, image_url)
VALUES 
('prod_serum_001', 'Luminous Hydrating Glow Serum (極光保濕超導精華液)', 1280.0000, 'https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=800&q=80'),
('prod_cream_002', 'Revitalizing Barrier Repair Cream (賦活屏障修護乳霜)', 1580.0000, 'https://images.unsplash.com/photo-1608248597359-bb47265ea5b3?w=800&q=80'),
('prod_oil_003', 'Gentle Botanical Cleansing Oil (植萃舒緩深層潔顏油)', 980.0000, 'https://images.unsplash.com/photo-1601049541289-9b1b7bbbfe19?w=800&q=80')
ON CONFLICT (product_id) DO NOTHING;
