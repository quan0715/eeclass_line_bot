from models import ChatStatus

__statuses:dict[str, callable]={}
__default_status:str|None=None
__invert_status_map:[callable, str]={}


def chat_status(status_id:str, default=False):
    def wrapper(func):
        __statuses[status_id]=func
        __invert_status_map[func]=[status_id]
        if default or len(__statuses)==0: 
            global __default_status
            __default_status=status_id
        return func
    return wrapper


def handle(event):
    assert __default_status is not None
    try:
        user_id = event.source.user_id
        status_exists = ChatStatus.objects.filter(line_user_id=user_id)
        if not status_exists:
            status=__default_status
            chat_status = ChatStatus(line_user_id=user_id, status=status)
            chat_status.save()
        else:
            status = ChatStatus.objects.get(line_user_id=user_id).status
        __statuses.get(status, __default_status)(event)
    except Exception as e:
        print(e)


def jump_to(func:callable, event):
    try:
        user_id = event.source.user_id
        status_exists = ChatStatus.objects.filter(line_user_id=user_id)
        if not status_exists:
            chat_status = ChatStatus(line_user_id=user_id)
        else:
            chat_status = ChatStatus.objects.get(line_user_id=user_id)
        chat_status.status = __invert_status_map[func]
        chat_status.save()
    except Exception as e:
        print(e)
