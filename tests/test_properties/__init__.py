from ppgc_backend.tests.activity.test_controller.test_objects import area_template

cover_image = {
    "secure_url":"http://example.com/cover.jpg",
    "public_id":"cover123"
}
other_images = [{
    "secure_url":"http://example.com/cover.jpg",
    "public_id":"cover124"
}]

# --- Step 2: Prepare payload
payload = {
    "title": "Luxury Apartment",
    "price": "500000.00",   # Decimal must be str in JSON
    "description": "A beautiful 3-bedroom apartment in Lekki",
    "availability": "available",
    "type": "apartment",
    "cover_image": cover_image,
    "other_images": other_images,
    "features": ["bedrooms", "bathrooms", "parking"],
    "area": {**area_template},
}