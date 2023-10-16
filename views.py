import requests
from django.shortcuts import render

# Create your views here.
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from linebot import LineBotApi, WebhookParser, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextSendMessage, FollowEvent, TemplateSendMessage, ButtonsTemplate, \
    MessageAction, PostbackAction, PostbackEvent

from notion_auth.models import LineUser
import uuid
from django.core.cache import cache
import time
import schedule
import asyncio
import aiohttp
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from eeclass_bot.EEAsyncBot import EEAsyncBot
# The URL of this server

UserID = 'Ub753911ef7aa5ef1a2e66e9ca365523e'
scheduler = BackgroundScheduler(timezone="Asia/Shanghai")

def check_user_info(user: LineUser) -> str:
    is_connect_with_notion = user.notion_token is not None
    print(user.eeclass_username, user.eeclass_password)
    is_connect_with_eeclass = user.eeclass_password is not None and user.eeclass_username is not None
    return f"""確認身份訊息\n \
Notion 資料庫連線 {is_connect_with_notion}\n \
EECLASS 連線 {is_connect_with_eeclass}\n \
如需連線 Notion 資料庫請打 notion 或 重新授權Notion\n \
如需連線 EECLASS 請說 eeclass\n \
    """
    # self.line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))

async def fetch_all_eeclass_data(account, password):
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        bot = EEAsyncBot(session, account, password)
        await bot.login()
        await bot.retrieve_all_course(check=True, refresh=True)
        await bot.retrieve_all_bulletins()
        all_bulletins_detail = await bot.retrieve_all_bulletins_details()
        await bot.retrieve_all_homeworks()
        all_homework_detail = await bot.retrieve_all_homeworks_details()
        await bot.retrieve_all_material()
        all_material_detail = await bot.retrieve_all_materials_details()
        return all_bulletins_detail, all_homework_detail, all_material_detail


def scheduling():
    line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
    message = TextSendMessage(text='成功獲取課程資料')
    coro = fetch_all_eeclass_data('111525026','Dn940387!')
    asyncio.run(coro)
    print(f'啟動: 目前時間{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    line_bot_api.push_message(UserID, message)

class LineBotCallbackView(View):
    line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
    parser = WebhookParser(settings.LINE_CHANNEL_SECRET)
    handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)
    server_url = "https://" + settings.ALLOWED_HOSTS[0]
    

    @csrf_exempt # 确保此视图可以处理 POST 请求
    def dispatch(self, request, *args, **kwargs):
        return super(LineBotCallbackView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # if request.method == 'POST':
        signature = request.META['HTTP_X_LINE_SIGNATURE']
        body = request.body.decode('utf-8')

        try:
            events = self.parser.parse(body, signature)
        except InvalidSignatureError:
            return HttpResponseForbidden()
        except LineBotApiError:
            return HttpResponseBadRequest()

        for event in events:
            if isinstance(event, MessageEvent):
                self.message_handler(event)
                # m_text = event.message.text
                # message = [TextSendMessage(text=m_text)]
                # line_bot_api.reply_message(event.reply_token, message)
            if isinstance(event, PostbackEvent):
                self.handle_postback(event)

        return HttpResponse()

    @handler.add(MessageEvent, message=TextSendMessage)
    def message_handler(self, event):
        print("==========Got You==========")
        print("User ID:", event.source.user_id)  # 打印出 User ID       
        text: str = event.message.text
        user_id = event.source.user_id
        user_exists = LineUser.objects.filter(line_user_id=user_id)
        if not user_exists:
            # 建立新的user資料
            print('建立新的資料')
            user = LineUser(line_user_id=user_id)
            user.save()
        else:
            user = LineUser.objects.get(line_user_id=user_id)

        if text == "重新授權Notion":
            state = str(uuid.uuid4())
            cache.set(state, user_id, timeout=300)
            message = f"請透過連結登入 {self.server_url}/notion/auth/{state}"
            self.line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))

        elif text.lower() == "notion":
            user_notion_token = LineUser.objects.get(line_user_id=user_id).notion_token
            state = str(uuid.uuid4())
            # print(user_notion_token)
            # print(state)
            cache.set(state, user_id, timeout=300)
            message = f"請透過連結登入 {self.server_url}/notion/auth/{state}" if not user_notion_token else f"使用者已經成功連線至Notion"

            self.line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))
        elif text == "設定":
            message = check_user_info(user)
            self.line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))
        elif text.lower() == "eeclass":
            button = TemplateSendMessage(
                alt_text= "eeclass 連線",
                template=ButtonsTemplate(
                    title='eeclass 連線設定',
                    text='請選擇連線設定',
                    actions=[
                        PostbackAction(
                            label='設定帳號',
                            data='action=設定帳號'
                        ),
                        MessageAction(
                            label='設定密碼',
                            text='設定密碼'
                        ),
                        MessageAction(
                            label='連線測試',
                            text='連線測試'
                        )
                    ]
                ))
            self.line_bot_api.reply_message(event.reply_token, button)


            #message = "輸入 帳號 <eeclass帳號>\n輸入 密碼 <eeclass密碼>"
        elif text == "排程":
            print("Scheduling Successful")
            button = TemplateSendMessage(
                alt_text= "Scheduling Button",
                template=ButtonsTemplate(
                    title='排程設定',
                    text='是否開啟排程',
                    actions=[
                        PostbackAction(
                            label='開啟排程',
                            data='開啟排程'
                        ),
                        PostbackAction(
                            label='關閉排程',
                            data='關閉排程'
                        )
                    ]
                ))
            self.line_bot_api.reply_message(event.reply_token, button)
            # if text=='關閉排程':
            #     print("Close Scheduling!")
            # scheduler.add_job(job1, 'interval', seconds=10)
            # scheduler.start()
            # seconds=5
            # minutes=1
        else:
            self.line_bot_api.reply_message(event.reply_token, TextSendMessage(text=text))

    @handler.add(PostbackEvent)
    def handle_postback(self, event):
        postback_data = event.postback.data  # This will contain 'action=set_password'
        print(postback_data)
        if postback_data == 'action=設定帳號':
            self.line_bot_api.reply_message(event.reply_token, TextSendMessage(text="輸入EECLASS帳號"))
        elif postback_data == '開啟排程':
            print("Start Scheduling!")
            if (scheduler.running):
                scheduler.resume()
            else:
                scheduler.start()
            # self.line_bot_api.reply_message(event.reply_token, TextSendMessage(text="排程更新開啟，設定每<min>分鐘更新一次"))
            button = TemplateSendMessage(
                alt_text= "Scheduling Button",
                template=ButtonsTemplate(
                    title='設定每<min>分鐘更新一次',
                    text='設定每<min>分鐘更新一次',
                    actions=[
                        PostbackAction(
                            label='10',
                            data='10'
                        ),
                        PostbackAction(
                            label='20',
                            data='20'
                        )
                    ]
                ))
            self.line_bot_api.reply_message(event.reply_token, button)
        elif postback_data == '關閉排程':
            print("Close Scheduling!")
            if scheduler.get_job('scheduling_job'):
                print("Removescheduling")
                scheduler.remove_job('scheduling_job')
                print(scheduler.get_job('scheduling_job'))
                scheduler.pause()  
                self.line_bot_api.reply_message(event.reply_token, TextSendMessage(text="排程更新關閉，如要開啟排程請點案開啟排程"))
            elif not (scheduler.state == 1):
                self.line_bot_api.reply_message(event.reply_token, TextSendMessage(text="排程尚未開啟!"))
                            
        elif postback_data == '10':
            if (scheduler.state == 2): # STATE_STOPPED
                self.line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請先開啟排程"))
            else:
                if scheduler.get_job('scheduling_job'):
                    print("Rescheduling_10")
                    print(scheduler.state)
                    scheduler.pause_job('scheduling_job')
                    scheduler.reschedule_job('scheduling_job', trigger='interval', seconds=10)
                    scheduler.resume_job('scheduling_job')
                    self.line_bot_api.reply_message(event.reply_token, TextSendMessage(text="已重新設定排程，每10s update"))
                else:
                    print("Newscheduling_10")
                    scheduler.add_job(scheduling, trigger='interval', seconds=10, id='scheduling_job')                   
                    self.line_bot_api.reply_message(event.reply_token, TextSendMessage(text="新增排程成功，每10s update"))
        elif postback_data == '20':
            if (scheduler.state == 2): # STATE_STOPPED
                self.line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請先開啟排程"))
            else:
                if scheduler.get_job('scheduling_job'):
                    print("Rescheduling_20")
                    print(scheduler.state)
                    scheduler.pause_job('scheduling_job')
                    scheduler.reschedule_job('scheduling_job', trigger='interval', seconds=20)
                    scheduler.resume_job('scheduling_job')
                    self.line_bot_api.reply_message(event.reply_token, TextSendMessage(text="已重新設定排程，每20s update"))                
                else:
                    print("Newscheduling_20")
                    scheduler.add_job(scheduling, trigger='interval', seconds=20, id='scheduling_job')
                    self.line_bot_api.reply_message(event.reply_token, TextSendMessage(text="新增排程成功，每20s update"))


    def connect_with_eeclass(self, message):
        pass
    @classmethod
    def update_auth_token(cls,user_id):
        cls.line_bot_api.push_message(user_id, TextSendMessage(text="與Notion連線成功"))
