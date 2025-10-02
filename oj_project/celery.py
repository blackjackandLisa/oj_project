import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oj_project.settings')

app = Celery('oj_project')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# 显式导入所有判题任务模块
app.autodiscover_tasks(['oj_project.judge'], related_name='tasks')
app.autodiscover_tasks(['oj_project.judge'], related_name='tasks_docker')
app.autodiscover_tasks(['oj_project.judge'], related_name='tasks_judge0')


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


