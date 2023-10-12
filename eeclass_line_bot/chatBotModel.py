from .chatBotExtension import chat_status, jump_to, text, button_group
from notion_auth.models import LineUser

@chat_status("default")
@button_group('EECLASS HELPER', '輸入以下指令開啟下一步', '輸入以下指令開啟下一步')
def default_message(event):
    jump_to(main_menu, event.source.user_id)
    return [
        'Notion Oauth連線',
        'EECLASS帳號設定',
        'EECLASS密碼設定',
        'EECLASS連線測試'
    ]

@chat_status("main menu")
@text
def main_menu(event):
    match event.message.text:
        case 'Notion Oauth連線':
            jump_to(oauth_connection, event.source.user_id, propagation=True)
            return
        case 'EECLASS帳號設定':
            jump_to(set_eeclass_account, event.source.user_id)
            return '請輸入你的EECLASS 帳號'
        case 'EECLASS密碼設定':
            jump_to(set_eeclass_password, event.source.user_id)
            return '請輸入你的EECLASS 密碼'
        case 'EECLASS連線測試':
            jump_to(eeclass_login_test, event.source.user_id, True)
            return
        case _:
            jump_to(default_message, event.source.user_id, True)
            return '沒有此項指令'


import uuid
from django.core.cache import cache
@chat_status("reply oauth link")
@text
def oauth_connection(event):
    state = str(uuid.uuid4())
    cache.set(state, event.source.user_id, timeout=300)
    u = f"https://www.notion.so/install-integration?response_type=code&client_id=5f8acc7a-6c3a-4344-b9e7-3c63a8fad01d&redirect_uri=https%3A%2F%2Fquan.squidspirit.com%2Fnotion%2Fredirect%2F&owner=user&state={state}"
    message = f"請透過連結登入 {u}"
    jump_to(default_message, event.source.user_id)
    return message
    

@chat_status("set eeclass account")
@text
def set_eeclass_account(event):
    try:
        user = LineUser.objects.get_or_create(line_user_id=event.source.user_id)[0]
        user.eeclass_username = event.message.text
        user.save()
        jump_to(default_message, event.source.user_id, True)
        return f'已更新你的帳號為 {event.message.text}'
    except Exception as e:
        return e

@chat_status("set eeclass password")
@text
def set_eeclass_password(event):
    # TODO 設定密碼
    user = LineUser.objects.get_or_create(line_user_id=event.source.user_id)[0]
    user.eeclass_password = event.message.text
    user.save()
    jump_to(default_message, event.source.user_id, True)
    return f'已更新你的密碼為 {event.message.text}'

import asyncio
from .eeclass import eeclass_test_login
@chat_status("test eeclass login")
@text
def eeclass_login_test(event):
    user = LineUser.objects.get_or_create(line_user_id=event.source.user_id)[0]
    login_success=False
    try:
        loop = asyncio.get_event_loop()
    except:
        loop=asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    try:
        task = loop.create_task(eeclass_test_login(user.eeclass_username, user.eeclass_password))
        loop.run_until_complete(task)
        login_success = task.result()
    except Exception as e:
        print(e)
    jump_to(default_message, event.source.user_id, True)
    if login_success:
        return '帳號認證成功'
    else:
        return '帳號認證失敗，請重新設定帳號密碼'
    