import vk_api

GROUP_ID = 185779488

with open('/home/abgde/vk_bot_key') as f:
    VK_BOT_TOKEN = f.read().strip()
    vk = vk_api.VkApi(token=s)
    api = vk.get_api()


def allowed(vk_user_id):
    res = api.messages.isMessagesFromGroupAllowed(group_id=GROUP_ID, user_id=vk_user_id)
    return res['is_allowed']
