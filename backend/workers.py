from celery import Celery
from celery.schedules import crontab
from app import create_app

flask_app = create_app()

celery = Celery(
    flask_app.import_name,
    broker=flask_app.config["CELERY_BROKER_URL"],
    backend=flask_app.config["CELERY_RESULT_BACKEND"],
)

celery.conf.beat_schedule = {
    "daily-trek-reminders": {
        "task": "tasks.send_daily_reminders",
        "schedule": crontab(hour=7, minute=0),
    },
    "monthly-activity-report": {
        "task": "tasks.generate_monthly_report",
        "schedule": crontab(hour=6, minute=0, day_of_month=1),
    },
}
celery.conf.timezone = "UTC"


class ContextTask(celery.Task):
    def __call__(self, *args, **kwargs):
        with flask_app.app_context():
            return self.run(*args, **kwargs)


celery.Task = ContextTask

import tasks  
