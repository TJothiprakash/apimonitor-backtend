"""
Email service for sending verification and password reset emails
"""
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List
from jinja2 import Template
from app.core.config import settings


class EmailService:
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.EMAILS_FROM_EMAIL
        self.from_name = settings.EMAILS_FROM_NAME

    async def send_email(
        self,
        to_emails: List[str],
        subject: str,
        html_content: str,
        text_content: str = None
    ):
        """Send email using SMTP"""
        try:
            message = MIMEMultipart("alternative")
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = ", ".join(to_emails)
            message["Subject"] = subject

            # Add text part if provided
            if text_content:
                text_part = MIMEText(text_content, "plain")
                message.attach(text_part)

            # Add HTML part
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)

            # Send email
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                start_tls=settings.SMTP_TLS,
                username=self.smtp_user,
                password=self.smtp_password,
            )
            
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False

    async def send_verification_email(self, to_email: str, username: str, token: str):
        """Send email verification email"""
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        
        html_template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Verify Your Email</title>
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #f8f9fa; padding: 30px; border-radius: 10px;">
                <h1 style="color: #333; text-align: center;">Welcome to API Monitor!</h1>
                <p>Hi {{ username }},</p>
                <p>Thank you for registering with API Monitor. Please verify your email address by clicking the button below:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{{ verification_url }}" 
                       style="background-color: #007bff; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Verify Email Address
                    </a>
                </div>
                
                <p>Or copy and paste this link in your browser:</p>
                <p style="word-break: break-all; color: #666;">{{ verification_url }}</p>
                
                <p><strong>This link will expire in 24 hours.</strong></p>
                
                <hr style="border: 1px solid #eee; margin: 30px 0;">
                <p style="color: #666; font-size: 12px;">
                    If you didn't create an account with us, please ignore this email.
                </p>
            </div>
        </body>
        </html>
        """)
        
        text_content = f"""
        Welcome to API Monitor!
        
        Hi {username},
        
        Thank you for registering with API Monitor. Please verify your email address by visiting:
        {verification_url}
        
        This link will expire in 24 hours.
        
        If you didn't create an account with us, please ignore this email.
        """
        
        html_content = html_template.render(
            username=username,
            verification_url=verification_url
        )
        
        return await self.send_email(
            to_emails=[to_email],
            subject="Verify Your Email - API Monitor",
            html_content=html_content,
            text_content=text_content
        )

    async def send_password_reset_email(self, to_email: str, username: str, token: str):
        """Send password reset email"""
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        
        html_template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Reset Your Password</title>
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #f8f9fa; padding: 30px; border-radius: 10px;">
                <h1 style="color: #333; text-align: center;">Password Reset Request</h1>
                <p>Hi {{ username }},</p>
                <p>We received a request to reset your password for your API Monitor account.</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{{ reset_url }}" 
                       style="background-color: #dc3545; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Reset Password
                    </a>
                </div>
                
                <p>Or copy and paste this link in your browser:</p>
                <p style="word-break: break-all; color: #666;">{{ reset_url }}</p>
                
                <p><strong>This link will expire in 15 minutes.</strong></p>
                
                <hr style="border: 1px solid #eee; margin: 30px 0;">
                <p style="color: #666; font-size: 12px;">
                    If you didn't request a password reset, please ignore this email. Your password will remain unchanged.
                </p>
            </div>
        </body>
        </html>
        """)
        
        text_content = f"""
        Password Reset Request
        
        Hi {username},
        
        We received a request to reset your password for your API Monitor account.
        
        Please visit the following link to reset your password:
        {reset_url}
        
        This link will expire in 15 minutes.
        
        If you didn't request a password reset, please ignore this email.
        """
        
        html_content = html_template.render(
            username=username,
            reset_url=reset_url
        )
        
        return await self.send_email(
            to_emails=[to_email],
            subject="Reset Your Password - API Monitor",
            html_content=html_content,
            text_content=text_content
        )


# Create email service instance
email_service = EmailService()
