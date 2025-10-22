from ppgc_backend.tests.activity.test_controller.test_objects import area_template

hotel_data_template = {
    "name": "Test Hotel",
    "description": "A nice place to stay.",
    "cover_image": {"secure_url": "https://example.com/img1.jpg", "public_id": "img1"},
    "other_images": [
        {"secure_url": "https://example.com/img1.jpg", "public_id": "img1"},
        {"secure_url": "https://example.com/img2.jpg", "public_id": "img2"}
    ],
    "area": {
        **area_template
    }
}

room_data_template = {
    "room_type": "suite",
    "room_number": "A101",
    "price_per_night": 3000,
    "max_occupancy": 4,
    "bed_count": 4,
    "amenities": ["WiFi", "AC", "TV"],
    "cover_image": {"secure_url": "https://example.com/img1.jpg", "public_id": "img1"},
    "other_images": [
        {"secure_url": "https://example.com/img1.jpg", "public_id": "img1"},
        {"secure_url": "https://example.com/img2.jpg", "public_id": "img2"}
    ],
}