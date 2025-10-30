from celery import shared_task
import time
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from .models import Follower

@shared_task
def send_welcome_email(username, email):
    """Simulates sending a welcome email to a new user."""
    print(f"Preparing welcome email for {username} ({email})...")
    time.sleep(5)  # Simulate time delay for sending email
    print(f"Email sent to {username}!")
    return f"Welcome email successfully sent to {email}"


@shared_task
def notify_followers(post_title, author_id):
    try:
        author = User.objects.get(id=author_id)
    except User.DoesNotExist:
        return f"Author with id {author_id} not found"
    
    # Get all users following this author
    followers_qs = Follower.objects.filter(follows=author)
    followers_emails = [f.user.email for f in followers_qs if f.user.email]

    subject = f"New Post form {author.username}"
    message = f"{author.username} just published a new post titled '{post_title}'.\n\nCheck it out!"
    from_email = settings.DEFAULT_FROM_EMAIL

    for email in followers_emails:
        send_mail(subject, message, from_email, [email])

    return f"Emails sent to {len(followers_emails)} followers."
