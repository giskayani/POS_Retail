"""
Product service: handles products and variants with id generation.
"""
from core.database import get_db
from core.id_generator import IDGenerator
from datetime import datetime
from bson import ObjectId

db = get_db()
_products = db.products
_variants = db.variants
id_gen = IDGenerator(db)

def create_product(name, category=None):
    """Create a product with auto-generated product_id."""
    products = db["products"]

    product_id = id_gen.get_next_id("PROD")

    doc = {
        "_id": product_id,
        "name": name,
        "category": category,
        "created_at": datetime.now()
    }
    products.insert_one(doc)
    return doc

def add_variant(product_id, name_or_list, price=None, stock=0, sku=None):
    """
    Add one or multiple variants to a product.
    name_or_list can be a single variant dict or a list of variants:
    Example single: name="Large", price=10000
    Example multiple: [
        {"name": "Small", "price": 8000, "stock": 10},
        {"name": "Medium", "price": 9000, "stock": 5}
    ]
    """
    products = db["products"]
    variants = db["variants"]

    product = products.find_one({"_id": product_id})
    if not product:
        raise ValueError("Product not found")

    new_variants = []

    # If input is a list --> multiple variants
    if isinstance(name_or_list, list):
        for v in name_or_list:
            variant_id = id_gen.get_next_id("VAR")
            new_variants.append({
                "_id": variant_id,
                "product_id": product_id,
                "name": v["name"],
                "price": v["price"],
                "stock": v.get("stock", 0),
                "sku": v.get("sku"),
                "created_at": datetime.now()
            })
    else:
        # Single variant
        variant_id = id_gen.get_next_id("VAR")
        new_variants.append({
            "_id": variant_id,
            "product_id": product_id,
            "name": name_or_list,
            "price": price,
            "stock": stock,
            "sku": sku,
            "created_at": datetime.now()
        })

    if new_variants:
        variants.insert_many(new_variants)
    return new_variants

def list_products_with_variants():
    """
    Return list of products and nested variants in a shape convenient for frontend.
    Each product includes a 'variants' array.
    """
    products = list(_products.find({}))
    # gather variants per product
    variants = list(_variants.find({}))
    var_map = {}
    for v in variants:
        pid = v["product_id"]
        var_map.setdefault(pid, []).append({
            "variant_id": v["variant_id"],
            "name": v["name"],
            "price": v["price"],
            "current_price": v.get("current_price", v["price"]),
            "stock": v.get("stock", 0),
            "sku": v.get("sku", "")
        })
    out = []
    for p in products:
        out.append({
            "product_id": p["product_id"],
            "name": p["name"],
            "category": p.get("category", ""),
            "variants": var_map.get(p["product_id"], [])
        })
    return out

def update_product(product_id: str, data: dict):
    """
    Update product fields (name, category).
    """
    data["updated_at"] = datetime.utcnow()
    res = _products.update_one({"product_id": product_id}, {"$set": data})
    return res.modified_count > 0

def update_variant(variant_id: str, data: dict):
    """
    Update variant fields (name, price, current_price, stock, sku).
    """
    data["updated_at"] = datetime.utcnow()
    res = _variants.update_one({"variant_id": variant_id}, {"$set": data})
    return res.modified_count > 0

def delete_product(product_id: str):
    """
    Delete product and all variants (logical delete optional).
    """
    _variants.delete_many({"product_id": product_id})
    res = _products.delete_one({"product_id": product_id})
    return res.deleted_count > 0

def delete_variant(variant_id: str):
    res = _variants.delete_one({"variant_id": variant_id})
    return res.deleted_count > 0
