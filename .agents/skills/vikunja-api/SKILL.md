---
name: vikunja-api
description: Use when creating, querying, updating, or deleting Vikunja projects, tasks, labels, assignees, comments, or views through the Vikunja REST API (/api/v1). Covers auth, conventions, key endpoints, and how to look up the full OpenAPI spec.
---

# Vikunja API

Full Swagger 2.0 spec: [references/vikunja-docs.json](references/vikunja-docs.json) (Vikunja v2.6.0). It is large; search it (grep for the path or `"summary"`) instead of reading it whole.

## Basics

- Base path: `/api/v1` on the configured Vikunja host (`<VIKUNJA_BASE_URL>`).
- Auth: `Authorization: Bearer <token>`. Use an API token (created via `PUT /tokens`) or a JWT from `POST /login`. Never hardcode or log tokens; read from an environment variable (`<VIKUNJA_API_TOKEN>`).
- Content type: `application/json`.
- Verb convention (differs from typical REST):
  - `GET` read
  - `PUT` create
  - `POST` update
  - `DELETE` delete
- Pagination: query `page`, `per_page`; response headers `x-pagination-total-pages`, `x-pagination-result-count`.
- Single-item responses include `x-max-permission` (0 read, 1 read/write, 2 admin).
- Errors: JSON `{code, message}`; check the HTTP status and `code`.
- Search: `s` query param. Filtering: `filter` query param (see https://vikunja.io/docs/filters), plus `sort_by`, `order_by`, `filter_timezone`, `filter_include_nulls`, `expand`.
- Dates are ISO 8601 strings. Update (`POST`) sends the full object; omitted fields may be reset to defaults, so fetch first and modify.

## Frequently used endpoints

<!-- TODO: fill in the endpoints you use most. Keep each entry to one line plus notes. -->

| Purpose | Method + path | Notes |
| --- | --- | --- |
| <TODO> | `<METHOD> /<path>` | <TODO: key params, body fields, gotchas> |
| <TODO> | `<METHOD> /<path>` | <TODO> |
| <TODO> | `<METHOD> /<path>` | <TODO> |

## Common workflows

<!-- TODO: describe step-by-step flows you want the agent to follow. -->

### <TODO: workflow name, e.g. "Create a task with labels and assignee">

1. <TODO>
2. <TODO>

### <TODO: workflow name>

1. <TODO>

## Request examples

<!-- TODO: add curl/Python examples for your most common calls. -->

```bash
curl -s -H "Authorization: Bearer $VIKUNJA_API_TOKEN" \
  "$VIKUNJA_BASE_URL/api/v1/<TODO>"
```

## Project-specific rules

<!-- TODO: defaults and guardrails, e.g. default project ID, label naming, confirm before delete. -->

- Default project ID: <TODO>
- Confirm with the user before any `DELETE` or bulk update.
- <TODO>

## Endpoint index (from spec)

Core groups for lookup; see the spec for parameters and schemas.

- Projects: `/projects`, `/projects/{id}`, `/projects/{projectID}/duplicate`, `/projects/{project}/views`
- Tasks: `/tasks`, `/tasks/{id}`, `/projects/{id}/tasks` (create), `/projects/{id}/views/{view}/tasks`, `/tasks/bulk`, `/projects/{project}/tasks/by-index/{index}`
- Task sub-resources: `/tasks/{taskID}/assignees`, `/tasks/{taskID}/comments`, `/tasks/{task}/labels`, `/tasks/{taskID}/labels/bulk`, `/tasks/{taskID}/relations`, `/tasks/{id}/attachments`, `/tasks/{id}/position`, `/tasks/{taskID}/duplicate`
- Kanban: `/projects/{id}/views/{view}/buckets`, `/projects/{project}/views/{view}/buckets/{bucket}/tasks`
- Labels: `/labels`, `/labels/{id}`
- Saved filters: `/filters`, `/filters/{id}`
- Teams/sharing: `/teams`, `/projects/{id}/users`, `/projects/{id}/teams`, `/projects/{project}/shares`
- Auth/tokens: `/login`, `/tokens`, `/routes`, `/user`
- Notifications/subscriptions: `/notifications`, `/subscriptions/{entity}/{entityID}`
- Webhooks: `/projects/{id}/webhooks`, `/webhooks/events`

Admin, migration, and testing endpoints exist but are out of scope unless explicitly requested.
