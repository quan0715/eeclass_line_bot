from unittest.mock import patch
import pytest

def fake_jump_to(func:callable, user_id, propagation=False):
    pass


class fake_event:
    class fake_source:
        def __init__(self, user_id):
            self.user_id=user_id

    class fake_message:
        def __init__(self, text):
            self.text=text
    
    def __init__(self, user_id, text):
        self.source=self.fake_source(user_id)
        self.message=self.fake_message(text)


patches = [
    patch('eeclass_line_bot.chatBotExtension.chat_status', lambda x:lambda y:y),
    patch('eeclass_line_bot.chatBotExtension.text', lambda x:x),
    patch('eeclass_line_bot.chatBotExtension.button_group', lambda *x:lambda y:y),
    patch('eeclass_line_bot.chatBotExtension.jump_to', fake_jump_to)
]

@pytest.fixture()
def event():
    import importlib
    import eeclass_line_bot.chatBotModel
    for patch in patches: patch.start()
    importlib.reload(eeclass_line_bot.chatBotModel)
    yield fake_event('test_id', 'test_message')
    for patch in patches: patch.stop()
    importlib.reload(eeclass_line_bot.chatBotModel)

def test_default_message(event):
    from eeclass_line_bot.chatBotModel import default_message
    assert default_message(event)==[
        'Notion Oauth連線',
        'EECLASS帳號設定',
        'EECLASS密碼設定',
        'EECLASS連線測試'
    ]

def test_main_menu(event):
    from eeclass_line_bot.chatBotModel import main_menu
    event.message.text='Notion Oauth連線'
    assert main_menu(event)==None
    event.message.text='EECLASS帳號設定'
    assert main_menu(event)=='請輸入你的EECLASS 帳號'
    event.message.text='EECLASS密碼設定'
    assert main_menu(event)=='請輸入你的EECLASS 密碼'
    event.message.text='EECLASS連線測試'
    assert main_menu(event)==None
    event.message.text='rdas;dklfj;klj'
    assert main_menu(event)=='沒有此項指令'

@patch('eeclass_line_bot.chatBotModel.cache')
def test_oauth_connection(cache, event):
    from eeclass_line_bot.chatBotModel import oauth_connection
    assert oauth_connection(event).startswith('請透過連結登入 ')

@pytest.mark.django_db
def test_set_eeclass_account(event):
    from eeclass_line_bot.chatBotModel import set_eeclass_account
    assert set_eeclass_account(event)==f'已更新你的帳號為 {event.message.text}'

@pytest.mark.django_db
def test_set_eeclass_password(event):
    from eeclass_line_bot.chatBotModel import set_eeclass_password
    assert set_eeclass_password(event)==f'已更新你的密碼為 {event.message.text}'

@pytest.mark.django_db
@patch('eeclass_line_bot.chatBotModel.eeclass_test_login')
def test_eeclass_login_test(eeclass_test_login, event):
    from eeclass_line_bot.chatBotModel import eeclass_login_test
    async def t(*args):return True
    async def f(*args):return False
    eeclass_test_login.side_effect = t
    assert eeclass_login_test(event)=='帳號認證成功'
    eeclass_test_login.side_effect = f
    assert eeclass_login_test(event)=='帳號認證失敗，請重新設定帳號密碼'