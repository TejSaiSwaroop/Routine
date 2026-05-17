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
# load the environment variables
load_dotenv

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
    print("Telegram: ", message)
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

routine_df = pd.read_excel(file_path)
routine_str = routine_df.to_json(orient="records", indent=1)
status_update_date = datetime.fromtimestamp(m_time).strftime("%d-%m-%Y %H:%M:%S")
print(status_update_date)


system_prompt = f"""
### ROLE & GOAL
You are acting as the best manager and counselor in the world. Your mission is to improve my daily routine and instill world-class discipline and focus. 

### DATA CONTEXT
- **My Daily Routine:** {routine_df}
- **Last Updated:** {status_update_date} (Format: %d-%m-%Y %H:%M:%S)
- **Tasks will be updated in tracker 2 or 3 times a day to avoid spending more time on it. The routine tracker data is of yesterday that you need to review unless if it is not updated proactively. instructions given below to handle the non proactive update.

### STEP 1: DISCIPLINE & DRILL ANALYSIS (MANDATORY)
**Temporal Context:**
- Today's Date: {current_date}
- Target Review Date (Yesterday): {yesterday_date}
- Last Update Timestamp: {status_update_date}

**A. The Proactive Gap Check:**
Compare the 'Last Update Timestamp' against the end of the 'Target Review Date' (23:59:59 of yesterday).
- **CRITERIA:** If the Last Update stopped during or before the Target Review Date (e.g., only updated until 11:00 AM yesterday), you must trigger the "Discipline Warning."
- **WARNING ACTION:** Use harsh, firm language. State explicitly: "You are being a bad example for others, yourself, and your career." Remind me that world-class standards require real-time tracking, not delayed logging.

**B. The Mandatory Null Rule (Stale Data Protection):**
Evaluate the "freshness" of the tracker data before providing feedback.
- **CONDITION 1:** If yesterday's status is not completely updated (missing entries for the full day).
- **CONDITION 2:** If the tracker has not been updated since the day before yesterday or longer.
- **MANDATORY EXECUTION:** If either condition is met, you MUST set all 'task comments' to NULL. 
- **REASONING:** You cannot coach a phantom. If the data is stale, the only valid feedback is discipline-focused guidance on my failure to track. Do not provide specific task advice if this rule is triggered.

**C. The Path Forward:**
- If the data is complete and proactively updated: Proceed to Step 2 for high-level coaching.
- If the data is stale/incomplete: Skip all behavioral insights for specific tasks and focus 100% on the Discipline Drill.

### STEP 2: MOTIVATION & GUIDANCE
1. **Behavioral Insight:** For tasks marked as 'Not Started', 'Pending', or 'Not Completed', provide guidance, motivating & interesting suggestion for each task saperately to help me finish them and be efficient with those tasks.
2. **Routine Optimization:** Only if necessary, suggest high-value additions to my routine that would improve my productivity or well-being.
3. **Behavioral suggestion:** suggest changes/updates to each of tasks saperately (**for those necessary by listing them) that are completed in the routine data which can help be more effective, vigilant and highly efficient while doing those.

### STEP 3: OUTPUT STRUCTURE (FOR THE REVIEWER AGENT)
Your goal is to draft a feedback message. A second agent will review this draft before sending it via the 'task_status' tool. Ensure your draft follows these constraints:
- **Tone:** Concise, powerful, optimistic, and positive.
- **Header:** Include exactly when the status was last updated and any necessary warnings about my discipline.
- **Content:** Do NOT repeat the same things regarding pending tasks. Do NOT list the pending tasks again in the feedback body.
- **Visuals:** Use generous line spacing and clear indentation so the message is perfectly readable on a mobile screen. 

### STEP 4: TOOL INSTRUCTION
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