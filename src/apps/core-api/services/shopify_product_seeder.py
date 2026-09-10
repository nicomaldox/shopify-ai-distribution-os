import os
import logging
import httpx
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

BLUEPRINT_PRODUCTS = [
    {
        "title": "Luminous Hydrating Glow Serum (極光保濕超導精華液)",
        "body_html": "<p>High-potency hydrating glow serum with multi-molecular hyaluronic acid and botanical antioxidants for radiant, glassy skin.</p>",
        "vendor": "Glow Skin Co",
        "product_type": "Skincare Serum",
        "tags": "Skincare, Serum, Hydration, Glow, Daily Routine",
        "price": "1280.00",
        "image_url": "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=800&q=80"
    },
    {
        "title": "Revitalizing Barrier Repair Cream (賦活屏障修護乳霜)",
        "body_html": "<p>Ultra-nourishing ceramide-rich barrier repair cream designed to soothe, restore, and lock in deep moisture for sensitive or dry skin.</p>",
        "vendor": "Glow Skin Co",
        "product_type": "Skincare Moisturizer",
        "tags": "Skincare, Cream, Barrier Repair, Moisturizer, Clean Beauty",
        "price": "1580.00",
        "image_url": "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=800&q=80"
    },
    {
        "title": "Gentle Botanical Cleansing Oil (植萃舒緩深層潔顏油)",
        "body_html": "<p>Gentle botanical emulsifying cleansing oil that dissolves impurities and waterproof makeup without stripping the natural skin barrier.</p>",
        "vendor": "Glow Skin Co",
        "product_type": "Skincare Cleanser",
        "tags": "Skincare, Cleanser, Cleansing Oil, Botanical, Clean Beauty",
        "price": "980.00",
        "image_url": "https://images.unsplash.com/photo-1601049541289-9b1b7bbbfe19?w=800&q=80"
    }
]

async def seed_blueprint_products_to_shopify() -> dict:
    """
    Pushes the 3 D2C Skincare blueprint products directly to the Shopify development store
    via Shopify Admin REST API.
    Idempotent: Skips products that already exist with the same title.
    Leaves any existing dummy products (such as 'test2') completely intact.
    """
    load_dotenv(override=True)
    shop = os.getenv("SHOPIFY_SHOP_DOMAIN", "0efjx4-fp.myshopify.com").strip()
    token = os.getenv("SHOPIFY_ADMIN_API_ACCESS_TOKEN", "").strip()

    if not token or not shop:
        raise ValueError("Shopify credentials missing in environment.")

    headers = {
        "X-Shopify-Access-Token": token,
        "Content-Type": "application/json"
    }
    base_url = f"https://{shop}/admin/api/2024-01"

    created_products = []
    skipped_products = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Fetch existing products from Shopify to prevent duplicate creation
        list_resp = await client.get(f"{base_url}/products.json?limit=50", headers=headers)
        list_resp.raise_for_status()
        existing_products = list_resp.json().get("products", [])
        existing_titles = {p["title"].strip(): p for p in existing_products}

        # 2. Iterate through blueprint products
        for bp in BLUEPRINT_PRODUCTS:
            title = bp["title"]
            if title in existing_titles:
                existing = existing_titles[title]
                logger.info(f"Product '{title}' already exists on Shopify (ID: {existing['id']}). Skipping creation.")
                skipped_products.append({
                    "title": title,
                    "shopify_id": existing["id"],
                    "reason": "ALREADY_EXISTS"
                })
                continue

            # Construct Shopify Product Creation payload
            payload = {
                "product": {
                    "title": bp["title"],
                    "body_html": bp["body_html"],
                    "vendor": bp["vendor"],
                    "product_type": bp["product_type"],
                    "tags": bp["tags"],
                    "status": "active",
                    "variants": [
                        {
                            "price": bp["price"],
                            "inventory_management": None, # Non-tracking for seamless demo purchasing
                            "requires_shipping": True
                        }
                    ],
                    "images": [
                        {
                            "src": bp["image_url"],
                            "alt": bp["title"]
                        }
                    ]
                }
            }

            logger.info(f"Pushing blueprint product to Shopify: '{title}' (Price: NT$ {bp['price']})...")
            create_resp = await client.post(f"{base_url}/products.json", headers=headers, json=payload)
            if create_resp.status_code in (200, 201):
                created_data = create_resp.json().get("product", {})
                shopify_id = created_data.get("id")
                handle = created_data.get("handle")
                images = created_data.get("images", [])
                cdn_image = images[0].get("src") if images else bp["image_url"]

                logger.info(f"Successfully created '{title}' on Shopify! ID: {shopify_id}, Handle: {handle}")
                created_products.append({
                    "title": title,
                    "shopify_id": shopify_id,
                    "handle": handle,
                    "price": bp["price"],
                    "shopify_cdn_image": cdn_image
                })
            else:
                logger.error(f"Failed to create '{title}' on Shopify: {create_resp.status_code} - {create_resp.text}")
                raise RuntimeError(f"Shopify product creation failed for '{title}': {create_resp.text}")

    return {
        "status": "SUCCESS",
        "created_count": len(created_products),
        "skipped_count": len(skipped_products),
        "created_products": created_products,
        "skipped_products": skipped_products
    }
