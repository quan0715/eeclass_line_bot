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
            # jump_to(oauth, event)
            return 'Notion OAuth 2.0 連結'
        case 'EECLASS帳號設定':
            return '請輸入你的EECLASS 帳號'
        case 'EECLASS密碼設定':
            return '請輸入你的EECLASS 密碼'
        case 'EECLASS連線測試':
            return 'EECLASS API - Login'
        case _:
            return default_message(event)