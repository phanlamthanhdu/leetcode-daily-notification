import os
import requests
import base64
import html
import json
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def gmail_auth():
    creds = None

    # Load credentials and token from environment variables (JSON strings)
    credentials_json = os.getenv("GMAIL_CREDENTIALS")
    token_json = os.getenv("GMAIL_TOKEN")

    if not credentials_json or not token_json:
        raise RuntimeError("Missing Gmail credentials or token environment variables.")

    # Convert JSON strings to actual dicts
    creds_dict = json.loads(token_json)

    # Build Credentials object from loaded data
    creds = Credentials.from_authorized_user_info(creds_dict, SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    return creds


def create_message(to, subject, message_text):
    message = MIMEText(message_text, "plain")
    message['to'] = to
    message['subject'] = subject
    message['from'] = f'LeetCode Daily Notifier <{to}>'
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    print(message)
    return {'raw': raw}

def send_message(service, user_id, message):
    sent = service.users().messages().send(userId=user_id, body=message).execute()
    print(f"✅ Email sent! Message ID: {sent['id']}")
    return sent

def get_leetcode_daily_problem():
    graphql_url = "https://leetcode.com/graphql"
    headers = {
        "Content-Type": "application/json",
        "Referer": "https://leetcode.com",
        "User-Agent": "Mozilla/5.0"
    }

    # Step 1: Get metadata for today's problem
    query_daily = {
        "query": """
        query {
          activeDailyCodingChallengeQuestion {
            date
            question {
              title
              titleSlug
              difficulty
              topicTags { name }
            }
          }
        }
        """
    }

    res = requests.post(graphql_url, json=query_daily, headers=headers)
    data = res.json()["data"]["activeDailyCodingChallengeQuestion"]
    q = data["question"]
    title = q["title"]
    slug = q["titleSlug"]
    difficulty = q["difficulty"]
    tags = ", ".join(tag["name"] for tag in q["topicTags"])
    link = f"https://leetcode.com/problems/{slug}/"

    # Step 2: Get problem content (HTML)
    query_content = {
        "query": """
        query getQuestionDetail($titleSlug: String!) {
          question(titleSlug: $titleSlug) {
            content
          }
        }
        """,
        "variables": {
            "titleSlug": slug
        }
    }

    res2 = requests.post(graphql_url, json=query_content, headers=headers)
    content_html = res2.json()["data"]["question"]["content"]

    # Convert HTML content to plain text (very basic strip)
    import re
    content_text = re.sub('<[^<]+?>', '', content_html)
    content_text = re.sub(r'\n{3,}', '\n\n', content_text).strip()
    content_text = html.unescape(content_text)
    # Final message
    email_body = f"""📌 LeetCode Daily Challenge ({data['date']})

🧠 Title: {title}
📈 Difficulty: {difficulty}
🏷️ Tags: {tags}
🔗 Link: {link}

📝 Problem Description:
{content_text[:4000]}
"""
    return title, email_body

def send_daily_email():
    creds = gmail_auth()
    service = build('gmail', 'v1', credentials=creds)
    subject, body = get_leetcode_daily_problem()
    message = create_message("phanlamthanhdu@gmail.com", f"📌 LeetCode Daily: {subject}", body)
    send_message(service, "me", message)
    # message = create_message("lamtngochan@gmail.com", f"📌 LeetCode Daily: {subject}", body)
    # send_message(service, "me", message)

# Run it
send_daily_email()