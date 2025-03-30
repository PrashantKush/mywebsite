import os
import requests
from datetime import datetime, timedelta
from msal import PublicClientApplication
import json
from typing import List, Dict
import openai  # We'll use OpenAI for summarization

class TeamsSummarizer:
    def __init__(self, client_id: str, client_secret: str, tenant_id: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.scopes = ['https://graph.microsoft.com/.default']
        self.app = PublicClientApplication(
            client_id=self.client_id,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}"
        )
        self.access_token = None
        self.team_id = None
        self.channel_id = None

    def authenticate(self):
        """Authenticate with Microsoft Graph API"""
        result = self.app.acquire_token_silent(self.scopes, account=None)
        if not result:
            result = self.app.acquire_token_interactive(scopes=self.scopes)
        
        if "access_token" in result:
            self.access_token = result["access_token"]
            return True
        return False

    def set_channel(self, team_id: str, channel_id: str):
        """Set the team and channel IDs"""
        self.team_id = team_id
        self.channel_id = channel_id

    def get_messages(self, days_back: int = 1) -> List[Dict]:
        """Get messages from the specified channel"""
        if not self.access_token or not self.team_id or not self.channel_id:
            raise ValueError("Please authenticate and set channel first")

        # Calculate the date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)

        # Format dates for the API
        start_date_str = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_date_str = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Get messages from the channel
        url = f"https://graph.microsoft.com/v1.0/teams/{self.team_id}/channels/{self.channel_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get("value", [])
        else:
            raise Exception(f"Failed to get messages: {response.text}")

    def generate_summary(self, messages: List[Dict]) -> str:
        """Generate a summary of the messages using OpenAI"""
        # Combine all message content
        combined_text = "\n".join([
            f"{msg.get('from', {}).get('user', {}).get('displayName', 'Unknown')}: {msg.get('body', {}).get('content', '')}"
            for msg in messages
        ])

        # Use OpenAI to generate summary
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates concise summaries of team messages."},
                    {"role": "user", "content": f"Please create a concise summary of these team messages:\n\n{combined_text}"}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating summary: {str(e)}"

    def post_summary(self, summary: str):
        """Post the summary back to the channel"""
        if not self.access_token or not self.team_id or not self.channel_id:
            raise ValueError("Please authenticate and set channel first")

        url = f"https://graph.microsoft.com/v1.0/teams/{self.team_id}/channels/{self.channel_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        message = {
            "body": {
                "content": f"📊 **Daily Summary**\n\n{summary}"
            }
        }
        
        response = requests.post(url, headers=headers, json=message)
        if response.status_code != 201:
            raise Exception(f"Failed to post summary: {response.text}")

def main():
    # You'll need to replace these with your actual values
    CLIENT_ID = "your_client_id"
    CLIENT_SECRET = "your_client_secret"
    TENANT_ID = "your_tenant_id"
    TEAM_ID = "your_team_id"
    CHANNEL_ID = "your_channel_id"
    OPENAI_API_KEY = "your_openai_api_key"

    # Initialize OpenAI
    openai.api_key = OPENAI_API_KEY

    # Create summarizer instance
    summarizer = TeamsSummarizer(CLIENT_ID, CLIENT_SECRET, TENANT_ID)

    try:
        # Authenticate
        if summarizer.authenticate():
            print("Successfully authenticated with Microsoft Graph API")
        else:
            print("Failed to authenticate")
            return

        # Set the channel
        summarizer.set_channel(TEAM_ID, CHANNEL_ID)

        # Get messages from yesterday
        messages = summarizer.get_messages(days_back=1)
        print(f"Retrieved {len(messages)} messages")

        # Generate summary
        summary = summarizer.generate_summary(messages)
        print("Generated summary successfully")

        # Post summary back to channel
        summarizer.post_summary(summary)
        print("Posted summary to channel successfully")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 