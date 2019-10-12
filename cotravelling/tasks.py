from cotravelling.celery import app
from cotravelling.vk import send_message
from cotravelling.utils import user_id_to_vk_id

from datetime import datetime

@app.task
def send_notification(user_id, message):
    send_message(user_id, message)

@app.task
def send_trip_notifications(user_ids, trip):
    trip_datetime = datetime.strptime(trip['datetime'][:-6], "%Y-%m-%dT%H:%M:%S")
    trip_date = trip_datetime.strftime("%A, %d %B")
    trip_page_date = trip_datetime.strftime("%Y-%m-%d")
    message = "Появилась новая поездка!\n {} &#10145;&#10145; {}\n {}\n Успей присоединиться!\n shareandsave.ru/findtrip/{}".format(trip['source'], trip['target'], trip_date, trip_page_date)
    for user_id in user_ids:
        vk_id = user_id_to_vk_id(user_id)
        send_notification.delay(vk_id, message)