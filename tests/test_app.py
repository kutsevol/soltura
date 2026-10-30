from httpx import AsyncClient


async def test_health_checks_database(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_index_renders_base_layout(client: AsyncClient) -> None:
    response = await client.get("/")

    assert response.status_code == 200
    assert "<h1>Soltura</h1>" in response.text
    assert "htmx.org" in response.text
