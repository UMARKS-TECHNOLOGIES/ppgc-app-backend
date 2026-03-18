import pytest
import uuid
import cloudinary.api
from httpx import AsyncClient


import pytest
from httpx import AsyncClient
import cloudinary.api


@pytest.mark.asyncio
async def test_upload_and_delete_images(client_fixture):
    httpx_client: AsyncClient = client_fixture["http_client"]

    test_image_path = "tests/test_image_mgt/test.jpg"

    files = [
        ("files", ("test1.jpg", open(test_image_path, "rb"), "image/jpeg")),
        ("files", ("test2.jpg", open(test_image_path, "rb"), "image/jpeg")),
    ]

    public_ids = []

    try:
        # --- Upload ---
        upload_response = await httpx_client.post(
            "/media/upload/",
            files=files
        )

        assert upload_response.status_code == 200
        data = upload_response.json()

        assert isinstance(data, list)
        assert len(data) == 2

        for item in data:
            assert "public_id" in item
            assert "secure_url" in item
            assert item["secure_url"].startswith("https://")

            public_ids.append(item["public_id"])

            # Verify asset exists
            resource = cloudinary.api.resource(item["public_id"])
            assert resource["public_id"] == item["public_id"]

        # --- Delete ---
        delete_response = await httpx_client.request(
            "DELETE",
            "/media/delete/",
            json={"public_ids": public_ids}
        )

        assert delete_response.status_code == 200
        delete_data = delete_response.json()

        for pid in public_ids:
            assert delete_data["deleted"][pid] == "deleted"

        # Verify deletion
        for pid in public_ids:
            with pytest.raises(cloudinary.api.NotFound):
                cloudinary.api.resource(pid)

    finally:
        # 🔥 Cleanup (runs even if test fails midway)
        if public_ids:
            try:
                cloudinary.api.delete_resources(public_ids)
            except Exception:
                # Avoid masking original test failure
                pass