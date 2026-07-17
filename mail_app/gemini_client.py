import json
import re
from openai import OpenAI


client = OpenAI(
    api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0IjoiZ3VpIiwidiI6IjAuMC4wIiwidSI6ImhGQzJXQjFJUnZtRFVNYWlIelhXd3c9PSIsInV1IjoiOFg5akR4aUZTQ3FDTU8vbHRzYzlTUT09IiwiaWF0IjoxNzc5MzMyMzA2fQ.gdzNIOhIp7WxIap_LiIgaq7dR4Lj2w7UEkn2XlvolG8",
    base_url="https://api.puter.com/puterai/openai/v1",
)


def safe_parse_json(content):
    """
    Safely parse JSON from AI response.
    Handles markdown wrapped JSON too.
    """

    try:
        return json.loads(content)

    except Exception:
        pass

    try:
        cleaned = re.sub(r"```json|```", "", content).strip()
        return json.loads(cleaned)

    except Exception:
        pass

    return None


def analyze_email_conversations(emails):
    """
    Analyze latest inbox emails and group conversations.
    """

    email_list = ""

    for idx, mail in enumerate(emails, start=1):
        email_list += f"""
EMAIL {idx}

SUBJECT: {mail.subject}
SENDER: {mail.sender}
DATE: {mail.email_date}
MESSAGE:
{mail.message[:300]}

----------------------------------------
"""

    prompt = f"""
You are an enterprise email intelligence assistant.

Analyze these emails.

Group them into conversation clusters.

STRICT RULES:
- Return ONLY valid JSON
- No markdown
- No explanation
- No extra text

Format:

{{
  "clusters": [
    {{
      "topic": "Conversation topic",
      "participants": [
        "participant 1",
        "participant 2"
      ],
      "summary": [
        "summary point 1",
        "summary point 2"
      ],
      "priority": "High / Medium / Low",
      "recommendation": "Suggested action"
    }}
  ]
}}

EMAILS:
{email_list}
"""

    response = client.chat.completions.create(
        model="google/gemini-2.5-flash",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1,
    )

    parsed = safe_parse_json(response.choices[0].message.content)

    if parsed:
        return parsed

    return {
        "clusters": [
            {
                "topic": "Parsing failed",
                "participants": [],
                "summary": ["Could not parse AI response."],
                "priority": "Low",
                "recommendation": "Retry analysis."
            }
        ]
    }


def summarize_thread(emails):
    """
    Summarize selected email thread.
    """

    email_text = ""

    for idx, mail in enumerate(emails, start=1):
        email_text += f"""
EMAIL {idx}

FROM: {mail.sender}
SUBJECT: {mail.subject}
DATE: {mail.email_date}
MESSAGE:
{mail.message[:500]}

----------------------------------------
"""

    prompt = f"""
You are an enterprise email thread analyzer.

STRICT RULES:
- Return ONLY valid JSON
- No markdown
- No explanation
- No extra text

Format:

{{
  "thread_start": "",
  "thread_end": "",
  "participants": [
    {{
      "name": "",
      "email": ""
    }}
  ],
  "discussion_summary": [
    "point 1",
    "point 2"
  ],
  "further_actions": [
    "action 1"
  ],
  "recommendation": ""
}}

THREAD:
{email_text}
"""

    response = client.chat.completions.create(
        model="google/gemini-2.5-flash",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1,
    )

    parsed = safe_parse_json(response.choices[0].message.content)

    if parsed:
        return parsed

    return {
        "thread_start": "Unknown",
        "thread_end": "Unknown",
        "participants": [],
        "discussion_summary": ["Could not parse AI response."],
        "further_actions": ["Retry summary."],
        "recommendation": "Retry."
    }