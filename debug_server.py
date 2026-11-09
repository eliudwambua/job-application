import asyncio
import httpx
from app.main import app

async def main():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        routes = ["/", "/opportunities", "/copilot/1", "/applications", "/profile"]
        for r in routes:
            try:
                resp = await client.get(r)
                print(f"ROUTE {r} -> STATUS {resp.status_code}")
                if resp.status_code >= 400:
                    print(f"BODY:\n{resp.text[:800]}")
            except Exception as e:
                import traceback
                print(f"EXCEPTION on {r}:")
                traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

