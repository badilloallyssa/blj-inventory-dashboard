# Tools

Python scripts for deterministic execution. Each script should be:

- **Standalone** — runnable directly from the command line
- **Input-driven** — accept inputs via CLI args or environment variables from `.env`
- **Focused** — one script, one job
- **Reliable** — same input should always produce the same output

## Usage

Run scripts from the project root:

```bash
python tools/script_name.py --arg value
```

Credentials and API keys are loaded from `.env` automatically via `python-dotenv`.

## Adding a New Tool

1. Create `tools/your_tool_name.py`
2. Load env vars with `from dotenv import load_dotenv; load_dotenv()`
3. Use `argparse` for CLI inputs
4. Print structured output (JSON preferred) to stdout
5. Reference it in the relevant workflow SOP
