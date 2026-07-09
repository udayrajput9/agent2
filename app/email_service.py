import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from jinja2 import Environment, FileSystemLoader

from app.config import settings
from app.models import TripPlan, User
from app.render import map_to_png

_env = Environment(loader=FileSystemLoader("app/templates"))


def send_trip_email(user: User, trip: TripPlan) -> None:
    plan = dict(trip.plan_json or {})
    plan.setdefault("id", trip.id)
    plan.setdefault("destination", trip.destination)
    plan.setdefault("duration_days", trip.duration_days)
    plan.setdefault("total_budget", trip.budget)
    plan.setdefault("budget_used", plan.get("budget_used", 0))

    png_bytes = map_to_png(plan)

    template = _env.get_template("email_template.html")
    html_body = template.render(user=user, plan=plan, app_url=settings.APP_URL)

    msg = MIMEMultipart("related")
    msg["Subject"] = f"Your trip to {plan.get('destination')} is ready!"
    msg["From"] = settings.GMAIL_EMAIL
    msg["To"] = user.email

    msg.attach(MIMEText(html_body, "html"))

    image = MIMEImage(png_bytes, _subtype="png")
    image.add_header("Content-ID", "<treasure_map_image>")
    image.add_header("Content-Disposition", "inline", filename="treasure_map.png")
    msg.attach(image)

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(settings.GMAIL_EMAIL, settings.GMAIL_SMTP_PASSWORD)
        server.sendmail(settings.GMAIL_EMAIL, [user.email], msg.as_string())
