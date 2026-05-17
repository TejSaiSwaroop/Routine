# imports
from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import sys
import pytz

# load the environment variables
load_dotenv

# 1. Get the current time explicitly in India Standard Time (IST)
ist = pytz.timezone('Asia/Kolkata')
now_ist = datetime.now(ist)
current_time_str = now_ist.strftime("%H:%M")
current_hour = now_ist.hour

# 2. Dynamically determine the evaluation window based on your 3 crons
if 6 <= current_hour < 10:  # Around 7:15 AM
    current_window = "MORNING_LOG"
    target_date_label = "Yesterday"
elif 11 <= current_hour < 15:  # Around 12:45 PM
    current_window = "AFTERNOON_PROGRESS"
    target_date_label = "Today (First Half)"
else:  # Around 11:20 PM (or manual triggers)
    current_window = "NIGHTY_LOCKDOWN"
    target_date_label = "Today (Full Day)"

deepseek_base_url = "https://api.deepseek.com/v1"
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
deepseek_model = "deepseek-chat"

current_date = datetime.now()
yesterday_date = current_date - timedelta(days=1)

# for Telegram
telegram_bot_token = os.getenv("TELEGRAM_TOKEN")
telegram_chatid = os.getenv("TELEGRAM_CHATID")

# Safety Check: Stop early if keys are missing
if not all([deepseek_api_key, telegram_bot_token, telegram_chatid]):
    print("❌ Critical Error: Missing required environment variables.")
    sys.exit(1)

# deeepseek model
deepseek = OpenAI(base_url=deepseek_base_url, api_key=deepseek_api_key)

def telegram(message):
    url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"

    payload = {"chat_id": telegram_chatid, "text": message, "parse_mode": "Markdown"} # Allows the AI to use *bold* and _italic_

    try:
        response = requests.post(url, data=payload)
        response.raise_for_status() # Check for errors
        return {"status": "Success", "platform": "Telegram"}
    except Exception as e:
        return {"status": "Error", "message": str(e)}

def task_status(task_comment,Overall_feedback): # completed_tasks, pending_tasks
    result = telegram(f"\n{task_comment}\n\n{Overall_feedback}") # {completed_tasks}\nPending tasks: {pending_tasks}\n
    if result['status'] == "Success":
        return {"recorded": "True"}
    else:
        return {"recorded": result["message"]}


task_status_json = {
    "name": "task_status",
    "description": "Record the status of tasks and send highly structured, formatted feedback to the user's mobile via Telegram. Tasks updated in tracker 2 or 3 times a day.",
    "parameters": {
        "type": "object",
        "properties": {
            "task_comment": {
                "type": "string",
                "description": (
                    "Highly structured suggestions for specific tasks. "
                    "start it with 'Discipline Drill or something similar with positive emoji."
                    "Use Telegram-compatible Markdown: *bold* for headers, emojis for bullet points (e.g., 🔴, 🟢, ⚡), but no * or other simple special charecters in texts. make sure good emojis are there as it makes it look good."
                    "and double line breaks between different tasks to ensure readability on a mobile screen."
                    "add root cause and quick win suggestions with highly positive, influential and energetic iputs."
                    "Format it exactly like a professional report."
                )
            },
            "Overall_feedback": {
                "type": "string",
                "description": (
                    "The final motivational push and routine optimization. "
                    "Use a clear header like '--- 🚀 ROUTINE BOOSTER ---', "
                    "include bold text for emphasis, and use emojis to make the message optimistic. "
                    "Ensure there is a clear separation from the task_comment using whitespace."
                )
            }
        },
        "required": ["task_comment", "Overall_feedback"],
        "additionalProperties": False
    }
}


tools = [{"type": "function", "function": task_status_json}]

def handle_tool_calls(tool_calls):
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        print(arguments)
        print(f"Tool called: {tool_name}", flush=True)
        tool = globals().get(tool_name) 
        result = tool(**arguments) if tool else {}
        results.append({"role": "tool","content": json.dumps(result),"tool_call_id": tool_call.id})
    return results

# root folder where your routine_agent.py is located
BASE_DIR = Path(__file__).resolve().parent

# file relative to project folder structure
file_path = BASE_DIR / "data" / "daily_routine.xlsx"

# 2. Get the file modification time (timestamp)
m_time = file_path.stat().st_mtime

# 1. Define the explicit India Standard Time timezone
ist_timezone = pytz.timezone('Asia/Kolkata')

routine_df = pd.read_excel(file_path)
routine_str = routine_df.to_json(orient="records", indent=1)
status_update_dt = datetime.fromtimestamp(m_time, tz=pytz.utc).astimezone(ist_timezone)
# 3. Format it cleanly into your string variable
status_update_date = status_update_dt.strftime("%d-%m-%Y %H:%M:%S")
print(status_update_date)

system_prompt = f"""
### ROLE & GOAL
You are acting as the world's premier performance coach, systems architect and personal counselor. Your mission is to audit daily routines, dismantle friction points and instill world-class discipline, focus and tracking accountability.

### TEMPORAL CONTEXT
- **Current Run Time:** {current_time_str} IST
- **Active Evaluation Window:** {current_window}
- **Target Analysis Data:** Data reflects '{target_date_label}' performance.
- **Data Last Updated:** {status_update_date} (Format: %d-%m-%Y %H:%M:%S)

---

### STEP 1: CURRENT WINDOW EXECUTION LOGIC (MANDATORY)
You must tailor your entire analytical lens to the active execution window. Execute the instructions below for **{current_window}** explicitly:

#### 🌅 CASE A: MORNING_LOG (7:15 AM IST Run)
* **Objective:** Audit the complete closure of **YESTERDAY'S** performance. 
* **Focus:** Review the absolute end-state of yesterday's tracker entries. Provide firm, direct guidance and actionable behavioral corrections on how yesterday's stumbles can be neutralized today.
* **Discipline Rule:** Apply full proactive gap checks. If yesterday went dark prematurely, trigger the Discipline Drill immediately.

#### ☀️ CASE B: AFTERNOON_PROGRESS (12:45 PM IST Run)
* **Objective:** Mid-day course correction and tactical execution check for **TODAY**.
* **Focus:** Review tasks updated up until midday today. Identify high-priority items that are still 'Pending' or 'Not Started'. Do NOT treat them as failures yet; instead, provide sharp, motivating and strategic suggestions to help clear them before the night locks down.
* **Tone Adjustment:** Highly driving, tactical, energetic, and focusing. Act as an active corner coach during a match.

#### 🌌 CASE C: NIGHTLY_LOCKDOWN (11:20 PM IST Run)
* **Objective:** Final operational review of **TODAY'S** full loop.
* **Focus:** Evaluate the total day's output. Provide structured behavioral suggestions for completed tasks to maximize future efficiency, and strategic advice for stumbles.
* **Core Finale requirement:** End this evaluation with an incredibly powerful, anchoring, positive and optimistic closing statement that reinforces growth mindset, absolute belief in potential, and relentless execution tomorrow.

---

### STEP 2: DISCIPLINE & DRILL ANALYSIS (MANDATORY GAP PROTECTION)
*Note: Only enforce data freshness parameters relevant to the target window.*

**A. The Proactive Gap Check:**
- If window is `MORNING_LOG`: Compare 'Last Update' against 23:59:59 of yesterday. 
- If window is `AFTERNOON_PROGRESS` or `NIGHTLY_LOCKDOWN`: Compare 'Last Update' against the current runtime today.
- **CRITERIA:** If tracking stopped prematurely (e.g., in the morning run, data cuts off at 11:00 AM yesterday; or in the night run, updates stopped at noon today), trigger the **"Discipline Warning."**
- **WARNING ACTION:** Use uncompromising, firm language. State explicitly: *"You are setting a bad example for your career, your potential, and your own system."* Remind me that elite performance leaves a complete paper trail.

**B. The Mandatory Null Rule:**
- **CONDITION:** If the target window's tracking data is incomplete, blank, or has gone completely stale for multiple tracking cycles.
- **EXECUTION:** You MUST bypass routine optimization entirely, and output `NULL` for all individual task comments. Focus 100% of the payload on the tracking breach and the behavioral path back to structure. You cannot coach a phantom dataset.

---

### STEP 3: BEHAVIORAL INSIGHTS & ROUTINE OPTIMIZATION
*Skip this section completely if the Mandatory Null Rule is triggered.*

1. **Pending/Not Started Tasks:** Provide a distinct, motivating, and highly practical micro-strategy or suggestion for *each applicable task separately* to eliminate friction and drive execution efficiency.
2. **Completed Tasks:** Select the highest-impact completed actions and suggest optimization adjustments—how to execute them even more vigilantly, cleanly, or efficiently next time.
3. **Systems Leveling:** Only if an underlying systemic pattern emerges, suggest a targeted high-value adjustment to the overall routine structure to elevate well-being or productivity.

---

### STEP 4: OUTPUT STRUCTURE (FOR THE REVIEWER AGENT)
Your draft will be ingested by a Reviewer/Editor Agent. Structure your string payload strictly using these distinct variable blocks:

* **Header:** State the current execution window timestamp, data freshness status and any active tracking alerts or discipline drills.
* **Task Feedback Block:** Clear, individual task breakdowns (or NULL if blocked by Step 2). Use deep line breaks, strict indentation and scannable tracking emojis (🟢, 🔴, ⚡) optimized completely for clean mobile screen readability.
* **Overall/Closing Feedback:** The macro-assessment of the state of play, followed by the mandatory window-specific closing alignment (tactical fuel for Afternoon, powerful optimistic anchor for Nightly).

Focus on drafting the most definitive, impactful and perfectly formatted feedback string possible.

### STEP 5: TOOL INSTRUCTION
When the final version is approved, the tool `task_status` will be used to deliver this. For now, focus on generating the most impactful, well-formatted feedback string possible.
"""

messages = [{"role": "system", "content": system_prompt}]
response = deepseek.chat.completions.create(model="deepseek-v4-pro", messages=messages)

# Save the response text
draft_feedback = response.choices[0].message.content

reviewer_prompt = f"""
### ROLE
You are a High-Performance Communications Editor. Your job is to take the draft feedback provided and refine it into a world-class mobile notification. 

### YOUR OBJECTIVE
1. **Remove unnecesasry words:** Delete any "AI-speak" (e.g., "Here is your feedback" or "Based on your data").
2. **Emoji Injection:** Add relevant, professional and motivating emojis (e.g., 🚀, ⏳, ⚖️, 🎯) at the start of key sections to make the message visually engaging on Telegram if they are already not present in each section in the response. This is mandatory.
3. **Tone Check:** Ensure the tone is highly positive, optimistic and powerful. If the draft feels "dry" inject energy into the words.
4. **Final Tool Execution:** Once the message is polished, you are the only agent authorized to call the `task_status` tool.
5. **Language:** language should be in English. This is mandatory. Check that as well and update if response is in any other language.

### VALIDATION RULES
- **Check Stale Warnings:** Ensure the warning about being a "bad example" is present if the status was not updated, but make it sound strong/hard and optimistic.
- **Check spaces/emiojis:** Check if there is good line space between each item ( add line spaces for each item to make it look good ) and whether there are emojis whereever it makes it look engaging, motivating and positive and add emojis. 

### TOOL USAGE
When you have the perfect message, call:
`task_status(task_comment, Overall_feedback)`

**Important:** Map the refined text to the correct parameters. If the first agent set `task_comment` to null due to stale data, respect that.
"""

# 2. Prepare the messages for the Reviewer Agent
reviewer_messages = [
    # Give the Reviewer its specific instructions
    {"role": "system", "content": reviewer_prompt},
    
    # Provide the original System Prompt as a "Reference" 
    {"role": "user", "content": f"FOR REFERENCE - These were the original instructions and data: \n\n{system_prompt}"},
    
    # Provide the actual draft that needs reviewing
    {"role": "user", "content": f"DRAFT TO REVIEW AND SEND: \n\n{draft_feedback}"},
    
    # Final command to trigger the tool
    {"role": "user", "content": "Review the draft against the original instructions. If it passes, call the 'task_status' tool with the refined, formatted content."}
]

reviewer_response = deepseek.chat.completions.create(model="deepseek-v4-flash", messages=reviewer_messages, tools=tools) # deepseek-v4-pro

finish_reason = reviewer_response.choices[0].finish_reason



if __name__ == "__main__":

    # If the LLM wants to call a tool, we do that!
    if finish_reason=="tool_calls":
        message = reviewer_response.choices[0].message
        tool_calls = message.tool_calls
        results = handle_tool_calls(tool_calls)