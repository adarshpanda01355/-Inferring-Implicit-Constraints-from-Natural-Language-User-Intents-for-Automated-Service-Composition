# RQ2 Generation Module

This folder contains the script used to generate LLM outputs for the RQ2 benchmark.

## What this script does

The script generates structured constraint predictions for selected methods and domains, then writes:

- per-request JSON outputs into each method folder
- raw non-JSON failures into llm_raw_failures
- optional run summary JSON (if report path is provided)

Main script:

- [generate_llm_outputs.py](generate_llm_outputs.py)

## Input files

The script reads:

- Prompt templates:
  - [../zeroshot/zero_shot_prompt.md](../zeroshot/zero_shot_prompt.md)
  - [../fewshot/few_shot_prompt.md](../fewshot/few_shot_prompt.md)
  - [../cot/CoT_prompt.md](../cot/CoT_prompt.md)
  - [../hybrid/hybrid_prompt.md](../hybrid/hybrid_prompt.md)
- Subset files:
  - [../data/travelrequests_subset.json](../data/travelrequests_subset.json)
  - [../data/healthcarerequests_subset.json](../data/healthcarerequests_subset.json)

## Output files

Generated outputs are written to:

- [../zeroshot/llm_outputs](../zeroshot/llm_outputs)
- [../fewshot/llm_outputs](../fewshot/llm_outputs)
- [../cot/llm_outputs](../cot/llm_outputs)
- [../hybrid/llm_outputs](../hybrid/llm_outputs)

Raw model failures are written to:

- [../zeroshot/llm_raw_failures](../zeroshot/llm_raw_failures)
- [../fewshot/llm_raw_failures](../fewshot/llm_raw_failures)
- [../cot/llm_raw_failures](../cot/llm_raw_failures)
- [../hybrid/llm_raw_failures](../hybrid/llm_raw_failures)

Optional summary snapshots can be stored in:

- [reports](reports)

## Prerequisites

Before running generation mode, make sure:

- Python is installed
- `openai` package is installed
- OpenAI API key is set in environment variable `OPENAI_API_KEY`

Install dependency:

```bash
pip install openai
```

Windows (PowerShell) API key setup:

```powershell
setx OPENAI_API_KEY "YOUR_API_KEY_HERE"
```

Optional default model setup:

```powershell
setx OPENAI_MODEL "gpt-5.4"
```

Important:

- After `setx`, open a new terminal before running commands.
- You can still override model/token/timeout values from CLI.

## How to run

Run from project root:

```bash
python RQ2/generation/generate_llm_outputs.py --dry-check --methods all --domains all
python RQ2/generation/generate_llm_outputs.py --methods all --domains all --model gpt-5.4 --temperature 0 --max-output-tokens 1800 --timeout-seconds 60 --max-attempts 3
```

Save dry-check or run summary JSON to a file:

```bash
python RQ2/generation/generate_llm_outputs.py --dry-check --methods all --domains all --report-path RQ2/generation/reports/dry_check_report.json
python RQ2/generation/generate_llm_outputs.py --methods all --domains all --report-path RQ2/generation/reports/full_run_summary.json
```

Overwrite behavior:

- By default, existing per-request output JSON files are not overwritten.
- If you want to replace existing outputs, add `--overwrite`.

Example:

```bash
python RQ2/generation/generate_llm_outputs.py --methods all --domains all --overwrite
```

## Run modes

The script supports two execution modes:

- Dry-check mode: validates prompts, subsets, and output routing without calling the API.
- Generation mode: calls the model API and writes outputs.

You can also select subsets of methods/domains:

- Methods: `zeroshot`, `fewshot`, `cot`, `hybrid`, or `all`
- Domains: `travel`, `healthcare`, or `all`

## How to read the generated summary (brief)

If you use `--report-path`, the generated JSON is a run summary.

Quickly check:

1. top-level status and timestamp
2. method/domain counts (successes/failures)
3. failure reasons (if any)
4. output routing paths

## Small technical implementation note

The implementation follows this flow:

1. Parse selected methods and domains from CLI.
2. Resolve the RQ2 root path and load prompt/subset files.
   All inputs are fetched from the RQ2 root: prompts from the strategy folders ([../zeroshot](../zeroshot), [../fewshot](../fewshot), [../cot](../cot), [../hybrid](../hybrid)) and subsets from [../data](../data).
3. Build request prompts by replacing only `{request_id}` and `{request_text}` placeholders.
4. Call the model with a strict JSON schema for constraint extraction.
5. Route valid outputs to method/domain output folders.
6. Route invalid/non-JSON outputs to raw failure folders.
7. Print and optionally save run summary JSON.

## Dependencies

Required Python packages:

- `openai`

If needed:

```bash
pip install openai
```

The script also uses standard Python libraries only.
