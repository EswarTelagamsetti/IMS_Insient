import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config

def send_password_email(to_email, name, password):
    """Send password to new user via email"""
    try:
        smtp_server = Config.MAIL_SERVER
        smtp_port = Config.MAIL_PORT
        sender_email = Config.MAIL_USERNAME
        sender_password = Config.MAIL_PASSWORD

        if not sender_email or not sender_password:
            print("Email credentials not configured. Password:", password)
            return True

        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = to_email
        message["Subject"] = "Welcome to Insient - Your Login Credentials"

        app_link = "imsinsient-production.up.railway.app"  

        body = f"""
        Dear {name},

        Welcome to Insient! Your account has been created successfully.

        Your login credentials are:
        Email: {to_email}
        Password: {password}

        👉 Click the link below to log in directly:
        {app_link}

        Please login to the system and change your password for security.

        Best regards,
        Insient Team
        """

        message.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        text = message.as_string()
        server.sendmail(sender_email, to_email, text)
        server.quit()

        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        print(f"Password for {name} ({to_email}): {password}")
        return False
