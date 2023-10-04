from .chatBotExtension import chat_status, jump_to

@chat_status("default")
def default_message(event):
    jump_to(main_menu, event)
    return """歡迎使用EECLASS HELPER，輸入以下指令開啟下一步\n\
Notion Oauth連線 \n\
EECLASS帳號設定\n\
EECLASS密碼設定\n\
EECLASS連線測試\n\
設定"""

@chat_status("main menu")
def main_menu(event):
    match event.message.text:
        case 'Notion Oauth連線':
            return oauth_connection(event)
        case 'EECLASS帳號設定':
            jump_to(set_eeclass_account, event)
            return '請輸入你的EECLASS 帳號'
        case 'EECLASS密碼設定':
            jump_to(set_eeclass_password, event)
            return '請輸入你的EECLASS 密碼'
        case 'EECLASS連線測試':
            jump_to(test_eeclass_login, event)
            return 'EECLASS API - Login'
        case _:
            return default_message(event)


import uuid
from django.core.cache import cache
@chat_status("reply oauth link")
def oauth_connection(event):
    state = str(uuid.uuid4())
    cache.set(state, event.source.user_id, timeout=300)
    u = f"https://www.notion.so/install-integration?response_type=code&client_id=5f8acc7a-6c3a-4344-b9e7-3c63a8fad01d&redirect_uri=https%3A%2F%2Fquan.squidspirit.com%2Fnotion%2Fredirect%2F&owner=user&state={state}"
    message = f"請透過連結登入 {u}"
    jump_to(default_message, event)
    return message

from notion_auth.models import LineUser
@chat_status("set eeclass account")
def set_eeclass_account(event):
    try:
        user = LineUser.objects.get_or_create(line_user_id=event.source.user_id)[0]
        user.eeclass_username = event.message.text
        user.save()
        return f'已更新你的帳號為 {event.message.text}\n' + default_message(event)
    except Exception as e:
        return e

@chat_status("set eeclass password")
def set_eeclass_password(event):
    # TODO 設定密碼
    user = LineUser.objects.get_or_create(line_user_id=event.source.user_id)[0]
    user.eeclass_password = event.message.text
    user.save()
    return f'已更新你的密碼為 {event.message.text}\n' + default_message(event)

@chat_status("test eeclass login")
def test_eeclass_login(event):
    # TODO 嘗試登入
    login_success=True
    if login_success:
        return '帳號認證成功\n' + default_message(event)
    else:
        return '帳號認證失敗，請重新設定帳號密碼\n' + default_message(event)
    
