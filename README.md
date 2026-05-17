# Routine Agent: Automated Discipline & Performance Tracking

An automated, multi-agent analytics assistant designed to monitor daily routines, evaluate performance logs, and deliver high-impact discipline feedback directly to a mobile device via Telegram.

## 🚀 Project Architecture

The system uses a two-stage generative logic chain to process raw execution metrics and enforce absolute tracking accountability:

1. **Agent 1 (The Coach/Manager):** Evaluates raw daily performance data against targets. If tracking data is stale or incomplete, it triggers the **Mandatory Null Rule**—skipping routine optimization entirely and pivoting to a strict, uncompromising Discipline Drill to correct behavioral drift.
2. **Agent 2 (The Editor/Reviewer):** Serves as the quality gate. It parses raw outputs into structured variables (`task_comment`, `Overall_feedback`), balances tough love with optimistic framing, and formats the final payload into high-impact, scannable Telegram Markdown.

---

## 🛠️ Tech Stack & Environment

*   **Language & Execution:** Python 3.12+ managed via `uv` (Astral) for deterministic, zero-activation environment isolation.
*   **IDE Workspace:** Cursor (optimized via localized workspace configurations).
*   **Automation:** GitHub Actions running on a custom cloud cron synchronized to India Standard Time (IST / UTC+5:30).

---

## 💻 Local Development

This project relies strictly on a machine-managed local virtual environment (`.venv`), omitting legacy global path activation.

### Prerequisites
Ensure you have `uv` installed on your machine.

### Setup & Installation
Clone the repository and synchronize the deterministic lockfile:
```bash
uv sync --locked