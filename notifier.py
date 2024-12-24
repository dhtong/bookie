import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
from twilio.rest import Client
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Fetch Twilio credentials
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')

# Initialize the Twilio client
twilio_client = Client(account_sid, auth_token)


class EmailSender:
    def __init__(self, config_path="./email_config.json"):
        self.config = self._load_config(config_path)
        self.smtp_server = self.config.get("smtp_server", "smtp.gmail.com")
        self.smtp_port = self.config.get("smtp_port", 587)
        self.sender_email = self.config.get("sender_email")
        self.password = self.config.get("password")

    def _load_config(self, config_path):
        try:
            with open(config_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            raise Exception(f"Email config file not found at {config_path}")

    def send_email(self, body, recipient_emails, subject = "Found flight"):
        # Create message
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = ', '.join(recipient_emails)
        msg['Subject'] = subject

        # Add body
        msg.attach(MIMEText(body))

        try:
            # Create SMTP session
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            
            # Login
            server.login(self.sender_email, self.password)
            
            # Send email
            server.send_message(msg)
            
            # Close connection
            server.quit()
            print("Email sent successfully!")
            
        except Exception as e:
            print(f"Failed to send email: {str(e)}")