# vikunja-assistant
## Manual Vikunja requests

Sample bodies are in `requests/split/`. Run from the repo root with `VIKUNJA_BASE_URL` and `VIKUNJA_API_TOKEN` set. Replace `{project_id}`, `{task_id}` as needed.

Create label:

```bash
curl -X PUT "$VIKUNJA_BASE_URL/api/v1/labels" \
  -H "Authorization: Bearer $VIKUNJA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d @requests/split/create_label.json
```

Create task:

```bash
curl -X PUT "$VIKUNJA_BASE_URL/api/v1/projects/{project_id}/tasks" \
  -H "Authorization: Bearer $VIKUNJA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d @requests/split/create_task.json
```

Set labels on task (replaces all existing labels):

```bash
curl -X POST "$VIKUNJA_BASE_URL/api/v1/tasks/{task_id}/labels/bulk" \
  -H "Authorization: Bearer $VIKUNJA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d @requests/split/add_labels_to_task.json
```

Add a single label to task:

```bash
curl -X PUT "$VIKUNJA_BASE_URL/api/v1/tasks/{task_id}/labels" \
  -H "Authorization: Bearer $VIKUNJA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d @requests/split/add_single_label_to_task.json
```

Set task as done:

```bash
curl -X POST "$VIKUNJA_BASE_URL/api/v1/tasks/{task_id}" \
  -H "Authorization: Bearer $VIKUNJA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d @requests/split/set_task_done.json
```

Update task:

```bash
curl -X POST "$VIKUNJA_BASE_URL/api/v1/tasks/{task_id}" \
  -H "Authorization: Bearer $VIKUNJA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d @requests/split/update_task.json
```

Delete task (no body):

```bash
curl -X DELETE "$VIKUNJA_BASE_URL/api/v1/tasks/{task_id}" \
  -H "Authorization: Bearer $VIKUNJA_API_TOKEN"
```
