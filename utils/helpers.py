import secrets
import string
from datetime import datetime, date

def generate_password(length=8):
    """Generate a random password"""
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

def calculate_experience(start_date):
    """Calculate experience from start date"""
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    today = date.today()
    delta = today - start_date
    
    if delta.days < 30:
        return f"{delta.days} days"
    elif delta.days < 365:
        months = delta.days // 30
        remaining_days = delta.days % 30
        if remaining_days > 0:
            return f"{months} months, {remaining_days} days"
        else:
            return f"{months} months"
    else:
        years = delta.days // 365
        remaining_days = delta.days % 365
        months = remaining_days // 30
        if months > 0:
            return f"{years} years, {months} months"
        else:
            return f"{years} years"
