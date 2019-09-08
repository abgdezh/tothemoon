import social_django.models

def user_id_to_vk_id(user_id):
    social_django_user = social_django.models.UserSocialAuth.objects.get(user_id=user_id)
    return social_django_user.uid
