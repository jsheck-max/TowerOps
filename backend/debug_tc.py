import asyncio, httpx, json

TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwczovL2FwaS53b3JreWFyZC5jb20vIiwiaWF0IjoxNzcwMjI1MzUyLCJleHAiOjE4MDE3NjEyOTIsIm5iZiI6MTc3MDIyNTM1MiwianRpIjoieE9WNkt1UTlNdjFoN3hNTCIsInN1YiI6IjE1ODkxNiIsInBydiI6Ijg3ZTBhZjFlZjlmZDE1ODEyZmRlYzk3MTUzYTE0ZTBiMDQ3NTQ2YWEiLCJlbWFpbCI6Imp1ZGFoc2hlY2tAb3V0bG9vay5jb20iLCJ0eXBlIjoiYXBpIn0.pdH5tUtYcbAODqn0IspqdxC5dITY3MzePFEfYd0kqoc"
hdrs = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"}

async def main():
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get("https://api.workyard.com/orgs/20752/projects?page=1", headers=hdrs)
        data = r.json()
        items = data.get("data", data) if isinstance(data, dict) else data
        if items:
            print("ALL KEYS:", list(items[0].keys()))
            print()
            print("FIRST PROJECT:")
            print(json.dumps(items[0], indent=2, default=str)[:3000])

asyncio.run(main())
