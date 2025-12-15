from fastapi import Request

def is_secure_request(request: Request) -> bool:
    return request.url.scheme == "https"