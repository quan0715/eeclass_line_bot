from .eeclass import fetch_all_eeclass_data
import asyncio
from datetime import datetime
from linebot.models import TextSendMessage
from notion_auth.models import LineUser

# 排程
def get_scheduling_job(user_id):
    def scheduling():
        from .views import LineBotCallbackView
        message = TextSendMessage(text='成功獲取課程資料')
        # TODO fix bug of following command
        user, created = LineUser.objects.get_or_create(line_user_id=user_id)
        coro = fetch_all_eeclass_data(user.eeclass_username,user.eeclass_password, user)
        asyncio.run(coro)
        print(f'啟動: 目前時間{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        LineBotCallbackView.push_message(user_id, message)
    return user_id
