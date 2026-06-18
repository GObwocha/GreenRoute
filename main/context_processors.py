from .models import DirectMessage

def unread_messages_count(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            count = DirectMessage.objects.filter(sender__is_superuser=False, is_read=False).count()
        else:
            count = DirectMessage.objects.filter(receiver=request.user, is_read=False).count()
        return {'unread_messages_count': count}
    return {'unread_messages_count': 0}
