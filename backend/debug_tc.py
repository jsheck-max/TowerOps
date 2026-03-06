import asyncio, httpx, json

TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwczovL2FwaS53b3JreWFyZC5jb20vIiwiaWF0IjoxNzcwMjI1MzUyLCJleHAiOjE4MDE3NjEyOTIsIm5iZiI6MTc3MDIyNTM1MiwianRpIjoieE9WNkt1UTlNdjFoN3hNTCIsInN1YiI6IjE1ODkxNiIsInBydiI6Ijg3ZTBhZjFlZjlmZDE1ODEyZmRlYzk3MTUzYTE0ZTBiMDQ3NTQ2YWEiLCJlbWFpbCI6Imp1ZGFoc2hlY2tAb3V0bG9vay5jb20iLCJ0eXBlIjoiYXBpIn0.pdH5tUtYcbAODqn0IspqdxC5dITY3MzePFEfYd0kqoc"
hdrs = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"}

async def main():
    async with httpx.AsyncClient(timeout=30) as c:
        found = 0
        for page in range(1, 6):
            r = await c.get(f"https://api.workyard.com/orgs/20752/time_cards?page={page}", headers=hdrs)
            data = r.json()
            items = data.get("data", data) if isinstance(data, dict) else data
            print(f"Page {page}: {len(items)} time cards")
            for tc in items:
                allocs = tc.get("cost_allocations", [])
                for alloc in allocs:
                    pid = alloc.get("org_project_id")
                    if pid:
                        proj = alloc.get("org_project", {})
                        pname = proj.get("name", "?") if isinstance(proj, dict) else "?"
                        print(f"  HIT: org_project_id={pid} name={pname}")
                        found += 1
                        if found >= 5:
                            return
        print(f"Total found with org_project_id: {found}")

asyncio.run(main())
