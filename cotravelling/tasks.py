from cotravelling.celery import app
from cotravelling.vk import send_message
from cotravelling.utils import user_id_to_vk_id

from datetime import datetime
from vk_api import exceptions

@app.task
def send_notification(user_id, message):
    try:
        print("Start new job. Sending message to user with id: {}".format(user_id))
        send_message(user_id, message)
    except ConnectionError:
        print("Could not send notification to user with id: {}".format(user_id))
    except exceptions.ApiError:
        print("Could not send notification to user with id: {}".format(user_id))
    except Exception:
        print("Error while executing")

@app.task
def send_trip_notifications(user_ids, trip):
    trip_datetime = datetime.strptime(trip['datetime'][:-6], "%Y-%m-%dT%H:%M:%S")
    trip_date = trip_datetime.strftime("%A, %d %B")
    trip_page_date = trip_datetime.strftime("%Y-%m-%d")
    message = "Появилась новая поездка!\n {} &#10145; {}\n {}\n Успей присоединиться!\n shareandsave.ru/findtrip/{}".format(trip['source'], trip['target'], trip_date, trip_page_date)
    for user_id in user_ids:
        vk_id = user_id_to_vk_id(user_id)
        send_notification.delay(vk_id, message)

@app.task
def send_user_join_notification(user_ids, trip, username):
    print("Start new task. Sending notification of new participant...")
    trip_datetime = datetime.strptime(trip['datetime'][:-1], "%Y-%m-%dT%H:%M:%S")
    trip_date = trip_datetime.strftime("%A, %d %B")
    message = "К вашей поездке {} &#10145; {} в {} присоединился новый участник (http://vk.com/{}), познакомьтесь с ним!".format(trip['source'], trip['target'], trip_date, username)
    for user_id in user_ids:
        vk_id = user_id_to_vk_id(user_id)
        send_notification.delay(vk_id, message)