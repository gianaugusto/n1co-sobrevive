# REST API

Base path `/api/v1`. Interactive docs at `/docs` (OpenAPI). All endpoints except `/health` need
`Authorization: Bearer <Auth0 access token>` with the permission shown below ([auth0-setup.md](auth0-setup.md)).

| Method & path | Permission | Description |
|---|---|---|
| `GET /health` | none | Liveness. |
| `POST /api/v1/processes` | `forget:write` | Start a forget process. `201` + process. `503` if Kafka rejects the message (the process stays `PENDING`). |
| `GET /api/v1/processes?limit=50&offset=0` | `forget:read` | Newest first. `limit` 1–200. |
| `GET /api/v1/processes/{id}` | `forget:read` | One process. `404` if unknown. |
| `POST /api/v1/processes/{id}/subscribers/{name}/retry` | `forget:write` | Republish for one **failed** subscriber. `202`; `404` unknown process/subscriber; `409` if it is not failed. |
| `GET /api/v1/subscribers` | `forget:read` | Registry of every subscriber ever seen. |

Errors: `401` missing/invalid token, `403` missing permission, `422` invalid body.

## Create

```http
POST /api/v1/processes
{ "tenant_id": "acme", "key": "jane@example.com", "type": "email" }
```

## Process object

```json
{
  "id": "6f1c1f44-…", "tenant_id": "acme", "key": "jane@example.com", "type": "email",
  "status": "IN_PROGRESS", "requested_at": "2026-01-01T12:00:00Z",
  "subscribers": [{
    "name": "billing", "started_at": "2026-01-01T12:00:03Z",
    "status": "FAILED", "attempt": 1,
    "results": [
      { "event": "STARTED", "detail": null, "occurred_at": "2026-01-01T12:00:03Z" },
      { "event": "FAILED", "detail": "timeout", "occurred_at": "2026-01-01T12:00:09Z" }
    ]
  }]
}
```
