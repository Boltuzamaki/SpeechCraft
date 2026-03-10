import asyncio

import httpx


async def send_callback(
    callback_url: str,
    payload: dict,
):
    """
    Asynchronously sends a POST request to the callback URL with a JSON
    payload. Implements retry logic with exponential backoff for
    production robustness.

    Args:
        callback_url (str): The URL to send the POST request to.
        payload (dict): The JSON payload to send.
    """
    headers = {"Content-Type": "application/json"}
    max_retries = 5
    base_delay = 1

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    callback_url, json=payload, headers=headers, timeout=15.0
                )
                response.raise_for_status()

                return
        except httpx.RequestError as e:  # noqa

            if attempt < max_retries - 1:
                delay = base_delay * (2**attempt)
                await asyncio.sleep(delay)
            else:

                raise
