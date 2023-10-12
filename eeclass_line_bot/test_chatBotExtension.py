import pytest

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

from eeclass_line_bot.chatBotExtension import text, button_group, jump_to, chat_status, handle
from eeclass_line_bot.chatBotExtension import get_func_status, get_status_func, get_user_status

@pytest.fixture
def event():
    yield fake_event('test_user_id', 'test_message')

def test_text(event):
    @text
    def return_message(e):
        return e.message.text
    assert return_message(event).text==event.message.text

def test_button_group(event):
    @button_group('title', 'text', 'default')
    def return_message_as_list(e):
        return list(e.message.text)
    
    for raw, button in zip(list(event.message.text), return_message_as_list(event).template.actions):
        assert raw==button.text

def test_chat_status():
    @chat_status('test status')
    def test(e):
        return 'test'
    
    assert get_status_func('test status')==test
    assert get_func_status(test)=='test status'

@pytest.mark.django_db
def test_jump_to(event):
    @chat_status('test status')
    def test(e):
        return 'test'
    
    jump_to(test, event.source.user_id)
    assert get_user_status(event.source.user_id)==get_func_status(test)

@pytest.mark.django_db
def test_handle(event):
    @chat_status('test status1')
    def test1(e):
        jump_to(return_message, e.source.user_id, propagation=True)
        return 'test1'
    
    @chat_status('test status2')
    def return_message(e):
        jump_to(test1, e.source.user_id, propagation=False)
        return e.message.text
    
    jump_to(test1, event.source.user_id)
    assert handle(event)==['test1', event.message.text]
    assert get_user_status(event.source.user_id)==get_func_status(test1)
