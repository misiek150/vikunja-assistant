# vikunja-assistant

Assistant that parses screenshots from school and kindergarten applications (e.g. Inso) using Google Gemini, extracts actionable tasks, and creates them in Vikunja with appropriate labels.

---

## Configuration & Environment Variables

Configuration is handled via Pydantic Settings. You can provide settings via a `.env` file in the repo root or as inline environment variables.

To get started, copy the template:

```bash
cp .env.example .env
```

Available options:

| Variable | Default | Description |
|---|---|---|
| `MOCK_MODE` | `false` | When `true`, Gemini is not called; canned/mock responses are used. |
| `MOCK_RESPONSES_DIR` | *(none)* | Optional directory with `<image_stem>.json` mock files. |
| `GEMINI_API_KEY` | *(none)* | Required when `MOCK_MODE=false`. Your Gemini API key. |
| `GEMINI_MODEL` | `gemini-3.8-flash` | Gemini model used for multimodal analysis. |
| `PROMPT_PATH` | *(none)* | Optional path to custom prompt markdown (defaults to `src/assistant/prompts/inso_extractor.md`). |
| `VIKUNJA_BASE_URL` | `http://localhost:3456` | Vikunja instance root URL. |
| `VIKUNJA_API_TOKEN` | *(none)* | Required API token with write permissions to the target project. |
| `VIKUNJA_PROJECT_ID` | `1` | ID of the Vikunja project where tasks will be created. |
| `SCREENSHOTS_DIR` | `./data/screenshots` | Directory watched for input screenshots. |
| `PROCESSED_DIR` | *(none)* | Directory for processed screenshots (defaults to `<SCREENSHOTS_DIR>/processed`). |
| `LOG_MODE` | `console` | `console` or `seq`. |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |

---

## Local Development & CLI Usage

Run commands with your virtual environment and `PYTHONPATH=src`:

```bash
# Optional alias for convenience:
alias run-assistant="PYTHONPATH=src .venv/bin/python -m assistant"
```

### 1. List detected screenshots (`read`)
```bash
PYTHONPATH=src .venv/bin/python -m assistant read
```

### 2. Test extraction & prompt without Vikunja (`analyze`)
Extracts tasks from an image and prints the JSON without making any Vikunja calls:

```bash
# Using mock mode:
PYTHONPATH=src MOCK_MODE=true .venv/bin/python -m assistant analyze --file data/screenshots/test.png

# Using live Gemini:
PYTHONPATH=src MOCK_MODE=false GEMINI_API_KEY="your-key" \
  .venv/bin/python -m assistant analyze --file data/screenshots/test.png
```

### 3. Test Vikunja request mapping (`map`)
Analyzes the screenshot and prints the resulting `PUT /projects/{id}/tasks` request payloads:

```bash
PYTHONPATH=src MOCK_MODE=true .venv/bin/python -m assistant map --file data/screenshots/test.png
```

### 4. Full pipeline in Dry-Run mode (`run --dry-run`)
Fetches label IDs from Vikunja (`GET /labels`), resolves label mapping and fallback `???` label, but **skips task creation and file moves**:

```bash
PYTHONPATH=src .venv/bin/python -m assistant run --dry-run
```

### 5. Full Live Run (`run`)
Runs the complete flow: extracts tasks, creates them in Vikunja, attaches labels in bulk, and moves processed screenshots to `processed/`:

```bash
PYTHONPATH=src .venv/bin/python -m assistant run
```

---

## Running with Docker

### Build the Docker image

```bash
docker build -t vikunja-assistant .
```

### Run the container

Pass your `.env` file and mount the screenshots directory:

```bash
docker run --rm \
  --env-file .env \
  -v $(pwd)/data/screenshots:/app/data/screenshots \
  vikunja-assistant run --dry-run
```

> **Note on networking:** If Vikunja is running on your host machine at `http://localhost:3456`, add `--network host` (on Linux) or set `VIKUNJA_BASE_URL=http://host.docker.internal:3456` so the container can connect to the host.

---

## Running Unit Tests

Run the test suite using pytest:

```bash
.venv/bin/pytest
```

---

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
