# Concourse Gate

**A door-staff kiosk and a shift worker that run on top of [Concourse](https://github.com/will-hamlin/concourse-demo), built to show cross-repository links in [Fiada](https://fiada.tech).**

Concourse Gate owns no data. Everything it does goes through Concourse: it imports Concourse's TypeScript types and client functions, and calls Concourse's FastAPI routes over HTTP from both TypeScript and Python. Import both repositories into one Fiada map and each of those connections becomes a dashed cross-repo edge, with the source that proves it.

```text
concourse-gate                               concourse-demo
──────────────                               ──────────────
kiosk/  (React + TS, :5190)
  hooks/gate.ts#useAdmission ─ call ──────→ web/src/client/checkins.ts#admitTicket ── HTTP ──→ backend/routes/checkins.py
  client/gate.ts ──────────── HTTP ────────→ backend/routes/{venues,tickets,schedules,alerts,checkins}.py
  types, errors, clockTime ─── import ─────→ web/src/types/*, web/src/client/errors.ts, web/src/components/layout/format.ts

sync/   (Python + httpx)
  concourse_sync/client.py ── HTTP ────────→ backend/routes/{analytics,alerts,venues,checkins,events}.py
```

| Part | What it does | Cross-repo links it makes |
|---|---|---|
| `kiosk/` | Door staff pick a room, scan a ticket ID, preview the holder, admit them, see the next session in that room, and report door problems. | **Imports**: Concourse's types (`@concourse/web/src/types/*`), its `admitTicket` client, `responseError`, and `clockTime`. **HTTP**: its own `fetch` calls to `/api/venues`, `/api/tickets`, `/api/schedules`, `/api/checkins`, `POST /api/alerts`. |
| `sync/` | A Python worker that writes an end-of-shift digest, raises crowding alerts when a room passes a threshold, and resolves them when it clears. | **HTTP** from Python: `/api/analytics`, `/api/analytics/refresh`, `/api/alerts`, `PATCH /api/alerts/{id}`, `/api/venues`, `/api/checkins`, `/api/events`. |

Admission is the interesting path: the kiosk doesn't reimplement it. Its `useAdmission` hook calls Concourse's own `admitTicket`, so Fiada shows **kiosk → Concourse client → Concourse API → service → database** as one chain across two repositories.

## See it in Fiada

1. Run Fiada ([instructions](https://github.com/tobygodat/hackgt13#run-it-locally)).
2. Add **both** repositories in the sidebar: `will-hamlin/concourse-demo` and this one (its GitHub name, or the absolute path to your checkout).
3. Leave **colour → layer**. Dashed edges are cross-repository. Open **concourse-gate → kiosk**, select the edge into `concourse-demo`, and read the contract: each interaction lists the import or request and the route it matched.
4. Switch **view → by function** to see Gate's code folded into Concourse's Checkins, Venues, Alerts and Analytics domains.

From a Fiada checkout you can also index both from the command line:

```sh
cd hackgt13/indexer
npm run index -- /path/to/concourse-demo /path/to/concourse-gate
```

**Verified with Fiada's indexer** (commit `16475d2`, both repositories indexed together): 40 cross-repo edges, all evidenced, none inferred: 13 HTTP (5 from the kiosk, 8 from the sync worker), 9 calls, 18 type references.

## Run it

Clone the two repositories side by side; the kiosk depends on Concourse's web package through `file:../../concourse-demo/web`.

```text
ai-agents/
  concourse-demo/
  concourse-gate/
```

Start Concourse first (API on :8010):

```sh
cd concourse-demo && npm install && npm run setup && npm run dev
```

**Kiosk** (http://localhost:5190, proxies `/api` to Concourse):

```sh
cd concourse-gate/kiosk && npm install && npm run dev
```

**Sync worker** (set `CONCOURSE_URL` if the API isn't on `http://127.0.0.1:8010`):

```sh
cd concourse-gate/sync
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m concourse_sync digest          # end-of-shift markdown summary
.venv/bin/python -m concourse_sync crowding        # raise alerts for rooms over 90%
.venv/bin/python -m concourse_sync clear           # resolve gate alerts that cleared
.venv/bin/python -m pytest                          # tests use a mock transport; no API needed
```

Admit a ticket in the kiosk, then open Concourse's dashboard: the check-in, the room's occupancy and the analytics all move, because there is only one system of record.

All data is Concourse's synthetic demo data.
