# Trello polling infrastructure

This repo includes a lightweight Trello polling pipeline for Sam's Playground.

## What it does

Every polling cycle it:

- fetches cards from the Trello board
- detects card state transitions using `pipeline/trello_state.json`
- auto-moves new `To Do` cards into `In Progress`
- emits JSON events for downstream builders/rework handlers
- checks GitHub PRs and auto-moves review cards to `Done` after merge
- appends a timestamped run log to `pipeline/trello_poll.log`

## Files

- `trello_pipeline.py` — main polling/detection logic
- `run_trello_poll.sh` — cron-safe wrapper that runs one polling cycle and logs output
- `trello-poll.cron` — sample cron entry for the required 10-minute schedule
- `trello_state.json` — persisted state across runs

## Manual usage

Run a single cycle:

```bash
python3 pipeline/trello_pipeline.py --once
```

Run continuously every 10 minutes:

```bash
python3 pipeline/trello_pipeline.py --loop --interval 600
```

Use the cron wrapper:

```bash
bash pipeline/run_trello_poll.sh
```

## Install the 10-minute cron job

From the repo root:

```bash
( crontab -l 2>/dev/null; cat pipeline/trello-poll.cron ) | crontab -
```

## Output contract

Each detected action is printed as one JSON object per line, for example:

```json
{"action":"new_pbi","card_id":"...","card_name":"...","card_url":"..."}
```

That makes it easy for a higher-level automation runner to consume and fan out to sub-agents.
