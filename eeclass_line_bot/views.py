from django.shortcuts import render

# Create your views here.
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from linebot import LineBotApi, WebhookParser, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextSendMessage
from concurrent.futures import ThreadPoolExecutor
from .chatBotExtension import handle
from .chatBotModel import *

# 排程
UserID = 'Ub753911ef7aa5ef1a2e66e9ca365523e'
scheduler = BackgroundScheduler(timezone="Asia/Shanghai")

# 排程
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

# 排程
def scheduling():
    line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
    message = TextSendMessage(text='成功獲取課程資料')
    coro = fetch_all_eeclass_data('帳號','密碼')
    asyncio.run(coro)
    print(f'啟動: 目前時間{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    line_bot_api.push_message(UserID, message)



class LineBotCallbackView(View):
    line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
    parser = WebhookParser(settings.LINE_CHANNEL_SECRET)
    handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)
    server_url = "https://quan.squidspirit.com"
    threadPoolExecutor = ThreadPoolExecutor()

    @csrf_exempt
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

        return HttpResponse()

    @handler.add(MessageEvent, message=TextSendMessage)
    def message_handler(self, event):
        def reply(event):
            replies=handle(event)
            for idx, reply in enumerate(replies):
                if idx==len(replies)-1: break
                self.line_bot_api.push_message(event.source.user_id, reply)
            if len(replies):
                self.line_bot_api.reply_message(event.reply_token, replies[-1])
        self.threadPoolExecutor.submit(reply, event)

        @handler.add(PostbackEvent)
    
    # 排程
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


    @classmethod
    def notion_auth_callback(cls, user_id):
        class fake_source:
            def __init__(self, user_id):
                self.user_id=user_id

        class fake_event:
            def __init__(self, user_id):
                self.source=fake_source(user_id)

        cls.line_bot_api.push_message(user_id, TextSendMessage(text="與Notion連線成功"))
        from .chatBotModel import default_message
        cls.line_bot_api.push_message(user_id, default_message(fake_event(user_id)))

