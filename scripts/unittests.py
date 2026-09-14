"""End-to-end smoke test for the endpoints built so far. Requires the dev auth bypass and a running server."""

import sys
from datetime import datetime

import requests

BASE = "http://localhost:8000"
STAMP = datetime.now().strftime("%H%M%S")

passed, failed = 0, 0


def check(label, response, expected_status, predicate=None):
    global passed, failed
    ok = response.status_code == expected_status
    if ok and predicate:
        try:
            ok = predicate(response.json())
        except Exception:
            ok = False
    if ok:
        passed += 1
        print(f"  PASS  {label}")
    else:
        failed += 1
        print(f"  FAIL  {label} — got {response.status_code}: {response.text[:200]}")
    return response


print("\nFoundation")
check("/api/me returns the dev user", requests.get(f"{BASE}/api/me"), 200,
      lambda d: "email" in d)
check("/api/me returns roles", requests.get(f"{BASE}/api/me"), 200,
      lambda d: isinstance(d["roles"], list) and "pm" in d["roles"])
check("/api/me hides internal fields", requests.get(f"{BASE}/api/me"), 200,
      lambda d: "clerk_user_id" not in d and "is_active" not in d)

print("\nReference vocabulary")
check("ten survey types", requests.get(f"{BASE}/api/reference/survey-types"), 200,
      lambda d: len(d) == 10 and "B2B" in d)

print("\nClients")
client_name = f"Smoke Test Client {STAMP}"
created = check("create client", requests.post(f"{BASE}/api/clients",
                json={"name": client_name}), 201, lambda d: d["name"] == client_name)
check("duplicate client rejected", requests.post(f"{BASE}/api/clients",
      json={"name": client_name}), 409)
check("new client appears in list", requests.get(f"{BASE}/api/clients"), 200,
      lambda d: any(c["name"] == client_name for c in d))

if created.status_code != 201:
    print("\nCannot continue without a client.")
    sys.exit(1)
client_id = created.json()["id"]

print("\nProjects — creation and validation")
rdr = f"RDR{STAMP}"
project = check("create project with survey type", requests.post(f"{BASE}/api/projects",
                json={"rdr_number": rdr, "survey_name": "Smoke Test Survey",
                      "client_id": client_id, "survey_type": "B2B"}), 201,
                lambda d: d["client"]["name"] == client_name and d["survey_type"] == "B2B")
check("duplicate RDR rejected", requests.post(f"{BASE}/api/projects",
      json={"rdr_number": rdr, "survey_name": "Dupe", "client_id": client_id}), 409)
check("unknown survey type rejected", requests.post(f"{BASE}/api/projects",
      json={"rdr_number": f"{rdr}X", "survey_name": "Bad type",
            "client_id": client_id, "survey_type": "Nonsense"}), 422)
check("unknown client rejected", requests.post(f"{BASE}/api/projects",
      json={"rdr_number": f"{rdr}Y", "survey_name": "Bad client",
            "client_id": 999999}), 422)
check("survey type is optional", requests.post(f"{BASE}/api/projects",
      json={"rdr_number": f"{rdr}Z", "survey_name": "No type",
            "client_id": client_id}), 201, lambda d: d["survey_type"] is None)

if project.status_code != 201:
    print("\nCannot continue without a project.")
    sys.exit(1)
project_id = project.json()["id"]

print("\nProjects — pool and self-assignment")
check("unclaimed project is in the pool", requests.get(f"{BASE}/api/projects/pool"), 200,
      lambda d: any(p["id"] == project_id for p in d))
check("pool items carry the nested client", requests.get(f"{BASE}/api/projects/pool"), 200,
      lambda d: all("client" in p and "name" in p["client"] for p in d))
check("self-assign succeeds", requests.post(
      f"{BASE}/api/projects/{project_id}/self-assign"), 200)
check("second self-assign rejected", requests.post(
      f"{BASE}/api/projects/{project_id}/self-assign"), 409)
check("claimed project leaves the pool", requests.get(f"{BASE}/api/projects/pool"), 200,
      lambda d: not any(p["id"] == project_id for p in d))
check("project detail loads", requests.get(f"{BASE}/api/projects/{project_id}"), 200,
      lambda d: d["rdr_number"] == rdr)
check("missing project is a 404", requests.get(f"{BASE}/api/projects/999999"), 404)
check("detail lists the PM as an owner", requests.get(f"{BASE}/api/projects/{project_id}"), 200,
      lambda d: any(o["role"] == "pm" for o in d["owners"]))
check("unclaimed project has no owners", requests.get(f"{BASE}/api/projects/{project_id}"), 200,
      lambda d: isinstance(d["owners"], list))

print(f"\n{passed} passed, {failed} failed\n")
sys.exit(1 if failed else 0)