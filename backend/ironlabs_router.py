"""IronLabs routing integration - calls the IronLabs model-select API for intelligent routing."""

import httpx
import logging
import os

logger = logging.getLogger(__name__)

IRONLABS_ROUTER_URL = 'https://irona-ai--model-select.modal.run'


async def ironlabs_model_select(
    messages: list,
    models: list,
    tradeoff: str = "latency"
) -> dict:
    """
    Call the IronLabs routing API to select the best model.

    Args:
        messages: List of message dicts [{"role": "user", "content": "..."}]
        models: List of model dicts [{"provider": "openai", "model": "gpt-4o-mini"}, ...]
        tradeoff: Optimization criteria - "latency", "cost", or "performance"

    Returns:
        dict with 'provider' and 'model' keys, or None if routing fails
    """
    api_key = os.environ.get('IRONLABS_API_KEY', '')
    router_url = os.environ.get('IRONLABS_ROUTER_URL', IRONLABS_ROUTER_URL)

    if not api_key:
        logger.warning("IRONLABS_API_KEY not set, skipping IronLabs routing")
        return None

    # Format payload as the SDK does internally
    llm_providers = [
        {"provider": m["provider"], "model": m["model"]}
        for m in models
    ]

    payload = {
        "messages": messages,
        "llm_providers": llm_providers,
        "topk_models": 1,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                router_url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("providers"):
                    selected = data["providers"][0]
                    logger.info(
                        f"IronLabs routing selected: {selected['provider']}/{selected['model']}"
                    )
                    return {
                        "provider": selected["provider"],
                        "model": selected["model"],
                    }
                elif data.get("error"):
                    logger.warning(f"IronLabs routing error: {data['error']}")
                    return None

            logger.warning(
                f"IronLabs routing returned status {response.status_code}: {response.text[:200]}"
            )
            return None

    except Exception as e:
        logger.warning(f"IronLabs routing unavailable: {e}")
        return None
