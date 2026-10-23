"""End-to-end smoke test for the endpoints built so far. Requires the dev auth bypass and a running server."""

import sys
from datetime import datetime, timedelta

import requests

# 127.0.0.1, not localhost: on Windows "localhost" resolves to ::1 first and each
# request pays ~2s waiting for that to fail before falling back to IPv4.
BASE = "http://127.0.0.1:8000"
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
untyped = check("survey type is optional", requests.post(f"{BASE}/api/projects",
                json={"rdr_number": f"{rdr}Z", "survey_name": "No type",
                      "client_id": client_id, "assign_me": False}), 201,
                lambda d: d["survey_type"] is None)
untyped_id = untyped.json()["id"]

if project.status_code != 201:
    print("\nCannot continue without a project.")
    sys.exit(1)
project_id = project.json()["id"]

print("\nProjects — pool and self-assignment")
check("creating a project claims it for the PM who logged it",
      requests.get(f"{BASE}/api/projects/{project_id}"), 200,
      lambda d: any(o["role"] == "pm" for o in d["owners"]))
check("a self-claimed project is not in the pool", requests.get(f"{BASE}/api/projects/pool"), 200,
      lambda d: not any(p["id"] == project_id for p in d))
check("a project logged for someone else waits in the pool",
      requests.get(f"{BASE}/api/projects/pool"), 200,
      lambda d: any(p["id"] == untyped_id for p in d))
check("pool items carry the nested client", requests.get(f"{BASE}/api/projects/pool"), 200,
      lambda d: all("client" in p and "name" in p["client"] for p in d))
check("unclaimed project has no owners", requests.get(f"{BASE}/api/projects/{untyped_id}"), 200,
      lambda d: d["owners"] == [])
check("claiming an unassigned project succeeds", requests.post(
      f"{BASE}/api/projects/{untyped_id}/self-assign"), 200)
check("second claim rejected", requests.post(
      f"{BASE}/api/projects/{untyped_id}/self-assign"), 409)
check("claimed project leaves the pool", requests.get(f"{BASE}/api/projects/pool"), 200,
      lambda d: not any(p["id"] == untyped_id for p in d))
check("an unclaimable role is rejected", requests.post(
      f"{BASE}/api/projects/{project_id}/self-assign", json={"role": "viewer"}), 422)
check("project detail loads", requests.get(f"{BASE}/api/projects/{project_id}"), 200,
      lambda d: d["rdr_number"] == rdr)
check("missing project is a 404", requests.get(f"{BASE}/api/projects/999999"), 404)
print("\nUsers and roles")
me = requests.get(f"{BASE}/api/me").json()
check("roles list has six entries", requests.get(f"{BASE}/api/roles"), 200,
      lambda d: len(d) == 6 and any(r["name"] == "admin" for r in d))
check("user list includes me with my roles", requests.get(f"{BASE}/api/users"), 200,
      lambda d: any(u["id"] == me["id"] and isinstance(u["roles"], list) for u in d))
check("unknown role rejected", requests.post(f"{BASE}/api/users/{me['id']}/roles",
      json={"role": "wizard"}), 422)
check("duplicate grant rejected", requests.post(f"{BASE}/api/users/{me['id']}/roles",
      json={"role": "pm"}), 409)
check("unknown user rejected", requests.post(f"{BASE}/api/users/999999/roles",
      json={"role": "pm"}), 404)
check("cannot deactivate yourself", requests.patch(f"{BASE}/api/users/{me['id']}",
      json={"is_active": False}), 409)
check("revoking a role not held is a 404",
      requests.delete(f"{BASE}/api/users/{me['id']}/roles/dp"), 404)

print("\nSend to scripting")
check("untyped project refuses to advance", requests.post(
      f"{BASE}/api/projects/{untyped_id}/send-to-scripting"), 422)
check("typed project advances", requests.post(
      f"{BASE}/api/projects/{project_id}/send-to-scripting"), 200,
      lambda d: d["stage"] == "SCRIPTING")
check("advancing twice is rejected", requests.post(
      f"{BASE}/api/projects/{project_id}/send-to-scripting"), 409)
check("missing project is a 404", requests.post(
      f"{BASE}/api/projects/999999/send-to-scripting"), 404)


print("\nScripting pool — scripters claim their own work")
# The dev user needs the scripter role to claim scripting work; already granted on a re-run.
requests.post(f"{BASE}/api/users/{me['id']}/roles", json={"role": "scripter"})
check("dev user now holds scripter", requests.get(f"{BASE}/api/me"), 200,
      lambda d: "scripter" in d["roles"])
check("a scripter cannot claim a project still in PM assignment", requests.post(
      f"{BASE}/api/projects/{untyped_id}/self-assign", json={"role": "scripter"}), 409)
check("a scripter claims a project that reached scripting", requests.post(
      f"{BASE}/api/projects/{project_id}/self-assign", json={"role": "scripter"}), 200)
check("the scripter shows as an owner alongside the PM",
      requests.get(f"{BASE}/api/projects/{project_id}"), 200,
      lambda d: {o["role"] for o in d["owners"]} >= {"pm", "scripter"})
check("a second scripter cannot claim the same project", requests.post(
      f"{BASE}/api/projects/{project_id}/self-assign", json={"role": "scripter"}), 409)
check("a PM cannot claim a project that has left PM assignment", requests.post(
      f"{BASE}/api/projects/{project_id}/self-assign", json={"role": "pm"}), 409)


print("\nChecklists, ETA and send to QA")
check("the scripting checklist is served from the backend",
      requests.get(f"{BASE}/api/reference/checklists/scripting"), 200,
      lambda d: sum(len(s["items"]) for s in d) == 11
                and {s["section"] for s in d} == {"Project setup", "Programming", "Testing"})
check("an unknown checklist is a 404",
      requests.get(f"{BASE}/api/reference/checklists/nonsense"), 404)

checklist = requests.get(f"{BASE}/api/reference/checklists/scripting").json()
item_ids = [i["id"] for s in checklist for i in s["items"]]

check("send to QA refuses with no ETA and nothing ticked", requests.post(
      f"{BASE}/api/projects/{project_id}/send-to-qa"), 422)
check("an ETA in the past is rejected", requests.put(
      f"{BASE}/api/projects/{project_id}/eta",
      json={"client_link_eta": "2020-01-01T15:00:00"}), 422)
check("a naive ETA is read as UK time and stored with an offset", requests.put(
      f"{BASE}/api/projects/{project_id}/eta",
      json={"client_link_eta": "2030-06-10T15:00:00"}), 200,
      lambda d: d["client_link_eta"] == "2030-06-10T14:00:00+00:00")
check("an ETA with an explicit offset is honoured", requests.put(
      f"{BASE}/api/projects/{project_id}/eta",
      json={"client_link_eta": "2030-06-10T15:00:00+03:00"}), 200,
      lambda d: d["client_link_eta"] == "2030-06-10T12:00:00+00:00")

check("send to QA still refuses with the checklist open", requests.post(
      f"{BASE}/api/projects/{project_id}/send-to-qa"), 422)
check("an unknown checklist item is rejected", requests.patch(
      f"{BASE}/api/projects/{project_id}/checklists/scripting",
      json={"items": {"not_a_real_item": "done"}}), 422)
check("an invalid state is rejected", requests.patch(
      f"{BASE}/api/projects/{project_id}/checklists/scripting",
      json={"items": {item_ids[0]: "maybe"}}), 422)
check("ticking one item persists it", requests.patch(
      f"{BASE}/api/projects/{project_id}/checklists/scripting",
      json={"items": {item_ids[0]: "done"}}), 200,
      lambda d: d["scripting_checklist_state"][item_ids[0]] == "done")
check("a second patch merges rather than replaces", requests.patch(
      f"{BASE}/api/projects/{project_id}/checklists/scripting",
      json={"items": {item_ids[1]: "na"}}), 200,
      lambda d: d["scripting_checklist_state"][item_ids[0]] == "done"
                and d["scripting_checklist_state"][item_ids[1]] == "na")
check("clearing an item removes it", requests.patch(
      f"{BASE}/api/projects/{project_id}/checklists/scripting",
      json={"items": {item_ids[1]: None}}), 200,
      lambda d: item_ids[1] not in d["scripting_checklist_state"])

check("send to QA refuses while any item is open", requests.post(
      f"{BASE}/api/projects/{project_id}/send-to-qa"), 422)
requests.patch(f"{BASE}/api/projects/{project_id}/checklists/scripting",
               json={"items": {i: "done" for i in item_ids[:-1]}})
check("not applicable counts as answered", requests.patch(
      f"{BASE}/api/projects/{project_id}/checklists/scripting",
      json={"items": {item_ids[-1]: "na"}}), 200,
      lambda d: d["scripting_checklist_state"][item_ids[-1]] == "na")
check("a complete checklist and an ETA let it through", requests.post(
      f"{BASE}/api/projects/{project_id}/send-to-qa"), 200,
      lambda d: d["stage"] == "QA")
check("sending to QA twice is rejected", requests.post(
      f"{BASE}/api/projects/{project_id}/send-to-qa"), 409)
check("an ETA cannot be set once the project has left QA", requests.put(
      f"{BASE}/api/projects/{untyped_id}/eta",
      json={"client_link_eta": "2030-06-10T15:00:00"}), 409)


print("\nQA checklist")
check("the QA checklist repeats scripting and adds its own testing",
      requests.get(f"{BASE}/api/reference/checklists/qa"), 200,
      lambda d: sum(len(s["items"]) for s in d) == 16
                and any(s["section"] == "QA testing" and len(s["items"]) == 4 for s in d)
                and any(s["derived"] for s in d))

qa_sections = requests.get(f"{BASE}/api/reference/checklists/qa").json()
qa_required = [i["id"] for s in qa_sections if not s["derived"] for i in s["items"]]
qa_derived = [i["id"] for s in qa_sections if s["derived"] for i in s["items"]][0]

check("send to client refuses while the QA checklist is open", requests.post(
      f"{BASE}/api/projects/{project_id}/send-to-client"), 422)
check("the sign-off cannot be ticked by hand", requests.patch(
      f"{BASE}/api/projects/{project_id}/checklists/qa",
      json={"items": {qa_derived: "done"}}), 422)
check("part-way through, the sign-off stays untouched", requests.patch(
      f"{BASE}/api/projects/{project_id}/checklists/qa",
      json={"items": {i: "done" for i in qa_required[:-1]}}), 200,
      lambda d: qa_derived not in d["qa_checklist_state"])
check("answering the last item ticks the sign-off automatically", requests.patch(
      f"{BASE}/api/projects/{project_id}/checklists/qa",
      json={"items": {qa_required[-1]: "na"}}), 200,
      lambda d: d["qa_checklist_state"][qa_derived] == "done")
check("clearing an item un-ticks the sign-off again", requests.patch(
      f"{BASE}/api/projects/{project_id}/checklists/qa",
      json={"items": {qa_required[-1]: None}}), 200,
      lambda d: qa_derived not in d["qa_checklist_state"])
check("re-answering restores it", requests.patch(
      f"{BASE}/api/projects/{project_id}/checklists/qa",
      json={"items": {qa_required[-1]: "done"}}), 200,
      lambda d: d["qa_checklist_state"][qa_derived] == "done")


print("\nThe run to launch")
# project_id is in QA with its checklist complete.
check("the PM confirms the link went to the client", requests.post(
      f"{BASE}/api/projects/{project_id}/send-to-client"), 200,
      lambda d: d["stage"] == "CLIENT_REVIEW" and d["sub_status"] == "AWAITING_CLIENT")
check("sending to the client twice is rejected", requests.post(
      f"{BASE}/api/projects/{project_id}/send-to-client"), 409)
check("launching before quotas is rejected", requests.post(
      f"{BASE}/api/projects/{project_id}/launch"), 409)

check("a change request needs a summary", requests.post(
      f"{BASE}/api/projects/{project_id}/client-changes", json={"summary": "   "}), 422)
check("client changes send it back to scripting", requests.post(
      f"{BASE}/api/projects/{project_id}/client-changes",
      json={"summary": "Reword Q4 and add an age break"}), 200,
      lambda d: d["stage"] == "SCRIPTING" and d["sub_status"] is None)
check("the reason is kept on the timeline",
      requests.get(f"{BASE}/api/projects/{project_id}/transitions"), 200,
      lambda d: d[0]["to_stage"] == "SCRIPTING" and "age break" in (d[0]["reason"] or ""))

# Back round the loop: QA again, then the client approves.
requests.post(f"{BASE}/api/projects/{project_id}/send-to-qa")
check("second pass reaches the client", requests.post(
      f"{BASE}/api/projects/{project_id}/send-to-client"), 200,
      lambda d: d["stage"] == "CLIENT_REVIEW")
check("client approval moves it to quotas", requests.post(
      f"{BASE}/api/projects/{project_id}/client-approved"), 200,
      lambda d: d["stage"] == "QUOTAS" and d["sub_status"] is None)
check("approving twice is rejected", requests.post(
      f"{BASE}/api/projects/{project_id}/client-approved"), 409)

check("launch opens at soft launch", requests.post(
      f"{BASE}/api/projects/{project_id}/launch"), 200,
      lambda d: d["stage"] == "LIVE" and d["sub_status"] == "SOFT_LAUNCH")
check("confirming soft launch opens it fully", requests.post(
      f"{BASE}/api/projects/{project_id}/confirm-soft-launch"), 200,
      lambda d: d["stage"] == "LIVE" and d["sub_status"] == "FULL_LAUNCH")
check("confirming a second time is rejected", requests.post(
      f"{BASE}/api/projects/{project_id}/confirm-soft-launch"), 409)

print("\nHold and resume")
check("a live project can be parked", requests.post(
      f"{BASE}/api/projects/{project_id}/hold"), 200,
      lambda d: d["stage"] == "ON_HOLD")
check("holding twice is rejected", requests.post(
      f"{BASE}/api/projects/{project_id}/hold"), 409)
check("resume restores the stage and sub-status it was parked from", requests.post(
      f"{BASE}/api/projects/{project_id}/resume"), 200,
      lambda d: d["stage"] == "LIVE" and d["sub_status"] == "FULL_LAUNCH")
check("resuming a project that is not held is rejected", requests.post(
      f"{BASE}/api/projects/{project_id}/resume"), 409)

check("the timeline records every move in order",
      requests.get(f"{BASE}/api/projects/{project_id}/transitions"), 200,
      lambda d: len(d) >= 10 and d[0]["to_stage"] == "LIVE"
                and all(r["changed_by_name"] for r in d))
check("transitions for a missing project are a 404",
      requests.get(f"{BASE}/api/projects/999999/transitions"), 404)


print("\nProject list — the query every queue runs")
check("the list returns a page and a total", requests.get(f"{BASE}/api/projects"), 200,
      lambda d: isinstance(d["items"], list) and d["total"] >= len(d["items"])
                and d["limit"] == 25 and d["offset"] == 0)
check("rows carry the nested client and their owners",
      requests.get(f"{BASE}/api/projects?limit=5"), 200,
      lambda d: all("name" in r["client"] and isinstance(r["owners"], list) for r in d["items"]))
check("filtering by stage returns only that stage",
      requests.get(f"{BASE}/api/projects?stage=LIVE"), 200,
      lambda d: all(r["stage"] == "LIVE" for r in d["items"]))
check("an unknown stage is rejected",
      requests.get(f"{BASE}/api/projects?stage=NONSENSE"), 422)
check("the scripting pool is stage plus nobody holding scripter",
      requests.get(f"{BASE}/api/projects?stage=SCRIPTING&unclaimed=scripter"), 200,
      lambda d: all(r["stage"] == "SCRIPTING"
                    and not any(o["role"] == "scripter" for o in r["owners"])
                    for r in d["items"]))
check("an unknown role for unclaimed is rejected",
      requests.get(f"{BASE}/api/projects?unclaimed=wizard"), 422)
check("mine returns only projects I hold a role on",
      requests.get(f"{BASE}/api/projects?mine=true&limit=100"), 200,
      lambda d: all(any(o["name"] == me["name"] for o in r["owners"]) for r in d["items"]))
check("search matches the RDR number",
      requests.get(f"{BASE}/api/projects?q={rdr}"), 200,
      lambda d: d["total"] >= 1 and all(rdr in r["rdr_number"] for r in d["items"]))
check("search matches the survey name",
      requests.get(f"{BASE}/api/projects?q=Staffing"), 200,
      lambda d: all("Staffing" in r["survey_name"] for r in d["items"]))
check("filtering by client works",
      requests.get(f"{BASE}/api/projects?client_id={client_id}"), 200,
      lambda d: d["total"] >= 2)
check("an unknown sort is rejected",
      requests.get(f"{BASE}/api/projects?sort=colour"), 422)
check("limit is capped", requests.get(f"{BASE}/api/projects?limit=500"), 422)
page_one = requests.get(f"{BASE}/api/projects?limit=1&offset=0").json()
page_two = requests.get(f"{BASE}/api/projects?limit=1&offset=1").json()
check("paging moves through the results",
      requests.get(f"{BASE}/api/projects?limit=1&offset=1"), 200,
      lambda d: page_one["items"][0]["id"] != page_two["items"][0]["id"]
                and d["total"] == page_one["total"])

print("\nDashboard")
# A project still in scripting with an ETA tomorrow — the only way to assert the
# dated tiles against real data, since nothing else in this run owes a date soon.
soon = check("create a project with a near-term ETA", requests.post(f"{BASE}/api/projects",
             json={"rdr_number": f"{rdr}D", "survey_name": "Dashboard fixture",
                   "client_id": client_id, "survey_type": "B2B"}), 201)
soon_id = soon.json()["id"]
requests.post(f"{BASE}/api/projects/{soon_id}/send-to-scripting")
tomorrow_uk = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT11:00:00")
check("its ETA lands tomorrow", requests.put(f"{BASE}/api/projects/{soon_id}/eta",
      json={"client_link_eta": tomorrow_uk}), 200,
      lambda d: d["client_link_eta"] is not None)

# An unclaimed project, so the pool count has something to find.
requests.post(f"{BASE}/api/projects",
              json={"rdr_number": f"{rdr}E", "survey_name": "Pool fixture",
                    "client_id": client_id, "assign_me": False})

check("counts come back in one call", requests.get(f"{BASE}/api/dashboard/counts"), 200,
      lambda d: len(d["by_stage"]) == 10 and d["by_stage"]["SCRIPTING"] >= 1
                and d["pool"] >= 1 and d["mine"] >= 1)
check("the upcoming list is ordered by date",
      requests.get(f"{BASE}/api/dashboard/upcoming?days=30"), 200,
      lambda d: [i["due_at"] for i in d] == sorted(i["due_at"] for i in d))
check("upcoming items name their kind and project",
      requests.get(f"{BASE}/api/dashboard/upcoming?days=30"), 200,
      lambda d: all(i["kind"] and i["rdr_number"] and i["client"] for i in d))
check("the ETA we set shows up as a commitment",
      requests.get(f"{BASE}/api/dashboard/upcoming?days=30"), 200,
      lambda d: any(i["kind"] == "client_eta" and i["project_id"] == soon_id for i in d))
check("the horizon is capped", requests.get(f"{BASE}/api/dashboard/upcoming?days=3650"), 422)
check("a short horizon returns no more than a long one",
      requests.get(f"{BASE}/api/dashboard/upcoming?days=1&include_overdue=false"), 200,
      lambda d: len(d) <= len(requests.get(f"{BASE}/api/dashboard/upcoming?days=30").json()))

check("the summary carries every tile", requests.get(f"{BASE}/api/dashboard/summary"), 200,
      lambda d: all(k in d for k in ("due_today", "due_tomorrow", "overdue", "soft_launch_due",
                                     "active", "by_stage", "my_due_today", "my_overdue",
                                     "my_active", "open_change_requests", "as_of")))
check("tomorrow's ETA is counted in due_tomorrow",
      requests.get(f"{BASE}/api/dashboard/summary"), 200,
      lambda d: d["due_tomorrow"] >= 1)
check("soft launch is zero until fieldwork snapshots exist",
      requests.get(f"{BASE}/api/dashboard/summary"), 200,
      lambda d: d["soft_launch_due"] == 0)
check("active excludes delivered and on-hold",
      requests.get(f"{BASE}/api/dashboard/summary"), 200,
      lambda d: d["active"] == sum(v for k, v in d["by_stage"].items()
                                   if k not in ("DELIVERED", "ON_HOLD")))

print("\nList filters added for the dashboard")
check("filter by survey type", requests.get(f"{BASE}/api/projects?survey_type=B2B"), 200,
      lambda d: all(r["survey_type"] == "B2B" for r in d["items"]))
check("an unknown survey type is rejected",
      requests.get(f"{BASE}/api/projects?survey_type=Nonsense"), 422)
check("filter by assigned person", requests.get(f"{BASE}/api/projects?assigned_to={me['id']}"), 200,
      lambda d: d["total"] >= 1 and all(r["owners"] for r in d["items"]))
check("overdue excludes delivered and on-hold work",
      requests.get(f"{BASE}/api/projects?overdue=true"), 200,
      lambda d: all(r["stage"] not in ("DELIVERED", "ON_HOLD") for r in d["items"]))
check("due_after narrows the window",
      requests.get(f"{BASE}/api/projects?due_after=2099-01-01T00:00:00"), 200,
      lambda d: d["total"] == 0)

print("\nChange requests")
cr = check("a PM can raise one against a project", requests.post(f"{BASE}/api/change-requests",
           json={"project_id": project_id, "title": "Add age x region crossbreak",
                 "description": "Client asked after delivery"}), 201,
           lambda d: d["status"] == "OPEN" and d["rdr_number"] == rdr
                     and d["raised_by_name"] and d["completed_at"] is None)
cr_id = cr.json()["id"]
check("a title is required", requests.post(f"{BASE}/api/change-requests",
      json={"project_id": project_id, "title": "  "}), 422)
check("an unknown project is rejected", requests.post(f"{BASE}/api/change-requests",
      json={"project_id": 999999, "title": "Nowhere"}), 422)
check("it lists against its project",
      requests.get(f"{BASE}/api/change-requests?project_id={project_id}"), 200,
      lambda d: any(c["id"] == cr_id for c in d))
check("open ones can be filtered",
      requests.get(f"{BASE}/api/change-requests?status=OPEN"), 200,
      lambda d: all(c["status"] == "OPEN" for c in d))
check("assigning it to someone works", requests.patch(f"{BASE}/api/change-requests/{cr_id}",
      json={"assigned_to": me["id"]}), 200,
      lambda d: d["assigned_to"] == me["id"] and d["assigned_to_name"] == me["name"])
check("my queue finds it", requests.get(f"{BASE}/api/change-requests?mine=true"), 200,
      lambda d: any(c["id"] == cr_id for c in d))
check("completing it stamps completed_at", requests.patch(f"{BASE}/api/change-requests/{cr_id}",
      json={"status": "COMPLETED"}), 200,
      lambda d: d["status"] == "COMPLETED" and d["completed_at"] is not None)
check("reopening it clears completed_at", requests.patch(f"{BASE}/api/change-requests/{cr_id}",
      json={"status": "IN_PROGRESS"}), 200,
      lambda d: d["completed_at"] is None)
check("an unknown change request is a 404",
      requests.patch(f"{BASE}/api/change-requests/999999", json={"title": "x"}), 404)
check("the project itself never moved stage",
      requests.get(f"{BASE}/api/projects/{project_id}"), 200,
      lambda d: d["stage"] == "LIVE")

print("\nProfile")
check("my profile carries an avatar field", requests.get(f"{BASE}/api/me"), 200,
      lambda d: "avatar" in d)
check("I can set my avatar", requests.patch(f"{BASE}/api/me", json={"avatar": "fox"}), 200,
      lambda d: d["avatar"] == "fox")
check("it persists", requests.get(f"{BASE}/api/me"), 200, lambda d: d["avatar"] == "fox")
check("I can clear it", requests.patch(f"{BASE}/api/me", json={"avatar": None}), 200,
      lambda d: d["avatar"] is None)
check("I cannot promote myself through it", requests.patch(f"{BASE}/api/me",
      json={"is_head_pm_override": True}), 200,
      lambda d: d["is_head_pm_override"] == me["is_head_pm_override"])


print("\nProject assignments")
staff_project = check("create a project to staff", requests.post(f"{BASE}/api/projects",
                      json={"rdr_number": f"{rdr}A", "survey_name": "Staffing test",
                            "client_id": client_id, "survey_type": "B2B"}), 201)
staff_id = staff_project.json()["id"]
check("the creating PM already owns it",
      requests.get(f"{BASE}/api/projects/{staff_id}"), 200,
      lambda d: any(o["role"] == "pm" and o["user_id"] == me["id"] for o in d["owners"]))

scripter = check("assign a scripter", requests.post(
                 f"{BASE}/api/projects/{staff_id}/assignments",
                 json={"user_id": me["id"], "role": "scripter"}), 201,
                 lambda d: d["role"] == "scripter" and d["user_id"] == me["id"] and d["name"])
check("the same person twice in one role is rejected", requests.post(
      f"{BASE}/api/projects/{staff_id}/assignments",
      json={"user_id": me["id"], "role": "scripter"}), 409)
check("unknown role rejected", requests.post(
      f"{BASE}/api/projects/{staff_id}/assignments",
      json={"user_id": me["id"], "role": "wizard"}), 422)
check("unknown user rejected", requests.post(
      f"{BASE}/api/projects/{staff_id}/assignments",
      json={"user_id": 999999, "role": "scripter"}), 422)
check("assigning on a missing project is a 404", requests.post(
      f"{BASE}/api/projects/999999/assignments",
      json={"user_id": me["id"], "role": "scripter"}), 404)
check("re-assigning the sitting PM is rejected", requests.post(
      f"{BASE}/api/projects/{staff_id}/assignments",
      json={"user_id": me["id"], "role": "pm"}), 409)
check("one person can hold two roles on a project",
      requests.get(f"{BASE}/api/projects/{staff_id}"), 200,
      lambda d: sum(1 for o in d["owners"] if o["user_id"] == me["id"]) == 2)

others = [u for u in requests.get(f"{BASE}/api/users").json()
          if u["id"] != me["id"] and u["is_active"]]
if others:
    other = others[0]
    check("a second person can be added", requests.post(
          f"{BASE}/api/projects/{staff_id}/assignments",
          json={"user_id": other["id"], "role": "qa"}), 201)
    check("two people can hold the same role", requests.post(
          f"{BASE}/api/projects/{staff_id}/assignments",
          json={"user_id": me["id"], "role": "qa"}), 201)
    check("both QAs show on the project",
          requests.get(f"{BASE}/api/projects/{staff_id}"), 200,
          lambda d: sum(1 for o in d["owners"] if o["role"] == "qa") == 2)
else:
    print("  SKIP  two-people-per-role checks (only one user in this database)")

scripter_id = scripter.json()["id"]
check("unassign returns the remaining owners", requests.delete(
      f"{BASE}/api/projects/{staff_id}/assignments/{scripter_id}"), 200,
      lambda d: all(a["role"] != "scripter" for a in d)
                and any(a["role"] == "pm" for a in d))
check("closing the same assignment twice is rejected", requests.delete(
      f"{BASE}/api/projects/{staff_id}/assignments/{scripter_id}"), 409)
check("unknown assignment is a 404", requests.delete(
      f"{BASE}/api/projects/{staff_id}/assignments/999999"), 404)
check("an assignment belonging to another project is a 404", requests.delete(
      f"{BASE}/api/projects/{untyped_id}/assignments/{scripter_id}"), 404)
check("the closed-out scripter is gone from detail",
      requests.get(f"{BASE}/api/projects/{staff_id}"), 200,
      lambda d: all(o["role"] != "scripter" for o in d["owners"]))


print(f"\n{passed} passed, {failed} failed\n")
sys.exit(1 if failed else 0)