import vk_api
import random

GROUP_ID = 185779488

with open('/local/abgde/vk_bot_key') as f:
    VK_BOT_TOKEN = f.read().strip()
    vk = vk_api.VkApi(token=VK_BOT_TOKEN)
    api = vk.get_api()


def allowed(vk_user_id):
    res = api.messages.isMessagesFromGroupAllowed(group_id=GROUP_ID, user_id=vk_user_id)
    return res['is_allowed']

def send_message(user_id, message):
    api.messages.send(user_id=user_id, random_id=random.randint(0, 10000), peer_id=-GROUP_ID, message=message)
