import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'warehouse.settings')

app = Celery('warehouse')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(['accounts', 'warehouse_app', 'store', 'prediction'])
app.conf.beat_schedule = {
    'send-expiry-notifications-every-day': {
        'task': 'store.tasks.send_expiry_notifications',
        'schedule': crontab(hour=0, minute=0),
    },
    'forecast-by-category-every-day': {
        'task': 'store.tasks.forecast_by_category',
        'schedule': crontab(hour=0, minute=0),
    },
}
