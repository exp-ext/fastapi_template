import asyncio
from src.conf import settings
import httpx
from httpx_socks import AsyncProxyTransport


API_URL = "https://api-inference.huggingface.co/models/ZB-Tech/Text-to-Image"
headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_BEARER}"}


async def query(payload):
    proxy_transport = AsyncProxyTransport.from_url(settings.SOCKS5)

    async with httpx.AsyncClient(transport=proxy_transport, timeout=60.0) as client:
        response = await client.post(API_URL, headers=headers, json=payload)
        return response.content


async def main():
    image_bytes = await query({
        "inputs": "сходить за хлебом",
    })

    with open("output_image.png", "wb") as f:
        f.write(image_bytes)


asyncio.run(main())
