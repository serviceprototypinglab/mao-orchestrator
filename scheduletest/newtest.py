from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
schedule_app = Flask(__name__)


scheduler = BackgroundScheduler()
scheduler.start()


@schedule_app.route('/scheduleRun', methods=['POST'])
def schedule_run():
    data = request.get_json()
    text = data.get('text')
    job = scheduler.add_job(printing_something, 'interval', seconds=3,
                            args=[text],  misfire_grace_time=None,
                            coalesce=True)
    return "job details: %s" % job


def printing_something(text):
    print("printing %s at %s" % (text, datetime.now()))
