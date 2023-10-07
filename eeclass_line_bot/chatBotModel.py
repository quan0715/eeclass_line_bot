import json
from .chatBotExtension import chat_status, jump_to, text, button_group
import aiohttp
from NotionBot.NotionClient import Notion
from typing import Dict

import aiohttp
from NotionBot import *
from NotionBot.base.Database import *
from NotionBot.object import *
from NotionBot.object.BlockObject import *

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
            jump_to(test_eeclass_login, event.source.user_id, True)
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
    

from notion_auth.models import LineUser
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

from eeclass_bot.EEAsyncBot import EEAsyncBot
import asyncio
@chat_status("test eeclass login")
@text
def test_eeclass_login(event):
    user = LineUser.objects.get_or_create(line_user_id=event.source.user_id)[0]
    login_success=False
    try:
        loop = asyncio.get_event_loop()
    except:
        loop=asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    try:
        task = loop.create_task(eeclass_test(user.eeclass_username, user.eeclass_password, user))
        loop.run_until_complete(task)
        login_success = task.result()
    except Exception as e:
        print(e)
    jump_to(default_message, event.source.user_id, True)
    if login_success:
        return '帳號認證成功'
    else:
        return '帳號認證失敗，請重新設定帳號密碼'
    

async def eeclass_test(account, password, user: LineUser):
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        bot = EEAsyncBot(session, account, password)
        if not await bot.login(): return False
        await bot.retrieve_all_course(check=True, refresh=True)
        await bot.retrieve_all_bulletins()
        all_bulletins_detail = await bot.retrieve_all_bulletins_details()
        await bot.retrieve_all_homeworks()
        all_homework_detail = await bot.retrieve_all_homeworks_details()
        await bot.retrieve_all_material()
        all_material_detail = await bot.retrieve_all_materials_details()
        notion_bot = Notion(user.notion_token)
        db = notion_bot.get_database(user.eeclass_db_id)
        await update_all_bulletin_info_to_notion_db(bot.bulletins_detail_list , db)
        await update_all_homework_info_to_notion_db(bot.homeworks_detail_list, db)
        await update_all_material_info_to_notion_db(bot.materials_detail_list, db)

def builtin_in_notion_template(db: Database, target):
    return BaseObject(
        parent=Parent(db),
        properties=Properties(
            Title=TitleValue(target['title']),
            Course=SelectValue(target['course']),
            ID=TextValue(target['ID']),
            Announce_Date=DateValue(NotionDate(**target['date'])),
            link=UrlValue(target['url']),
            label=SelectValue("公告")
        ),
        children=Children(
            CallOutBlock(f"發佈人 {target['發佈人']}  人氣 {target['人氣']}", color=Colors.Background.green),
            QuoteBlock(f"內容"),
            ParagraphBlock(target['content']["公告內容"]),
            ParagraphBlock(" "),
            QuoteBlock(f"連結"),
            *[ParagraphBlock(TextBlock(content=links['名稱'], link=links['連結'])) for links in
              target['content']['連結']],
            ParagraphBlock(" "),
            QuoteBlock(f"附件"),
            *[ParagraphBlock(TextBlock(content=links['名稱'], link=links['連結'])) for links in
              target['content']['附件']],
        ),
        icon=Emoji("🐶"),
    )


def homework_in_notion_template(db: Database, target):
    cover_file_url = "https://images.pexels.com/photos/13010695/pexels-photo-13010695.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1"
    children_list = []
    for key, value in target['content'].items():
        children_list.append(QuoteBlock(TextBlock(key.capitalize()), color=Colors.Text.red))
        if key == 'attach' or key == 'link':
            children_list.extend([
                BulletedBlock(TextBlock(content=a['title'], link=a['link'])) for a in value
            ])
        else:
            result = TextBlock.check_length_and_split(value)
            text = [TextBlock(r) for r in result] if result else [TextBlock(value)]
            children_list.append(ParagraphBlock(*text)),

        children_list.append(DividerBlock()),

    return BaseObject(
        parent=Parent(db),
        properties=Properties(
            Title=TitleValue(target['title']),
            Course=SelectValue(target['course']),
            ID=TextValue(target['ID']),
            Deadline=DateValue(NotionDate(**target['date'])),
            link=UrlValue(target['url']),
            label=SelectValue("作業")
        ),
        children=Children(*children_list),
        icon=Emoji("🐶"),
        cover=FileValue(cover_file_url)
    )

def material_in_notion_template(db: Database, target):
    complete_emoji = "✅" if target['已完成'] else "❎"
    return BaseObject(
        parent = Parent(db),
        properties = Properties(
            Title = TitleValue(target['title']),
            Course = SelectValue(target['course']),
            ID = TextValue(target['ID']),
            # Deadline = DateValue(NotionDate(**target['deadline'])),
            link = UrlValue(target['url']),
            label = SelectValue("教材")
        ),
        children = Children(
            # CallOutBlock(f"發佈人 {target['發佈者']}  觀看數 {target['觀看數']}  教材類型 {target['subtype']}", color=Colors.Background.green),
            CallOutBlock(f"教材類型 {target['subtype']}", color=Colors.Background.green),
            CallOutBlock(f"完成條件: {target['完成條件']}  進度: {target['完成度']}  已完成: " + complete_emoji, color=Colors.Background.red),

        )
    )

# def get_config():
#     load_dotenv()
#     auth = os.getenv("NOTION_AUTH")
#     notion_bot = Notion(auth)
#     db: Database = notion_bot.search("CONFIG")
#     db_table = db.query_database_dataframe()
#     table = {
#          k: v for k, v in zip(db_table['KEY'], db_table['VALUE'])
#     }
#     return {
#         "DATABASE_NAME": table['DATABASE_NAME'],
#         "ACCOUNT": table['STUDENT_ID'],
#         "PASSWORD": table['PASSWORD'],
#     }

# just for testing

def get_id_col(db_col: List[Dict]) -> List[str]:
    return [p['properties']['ID']['rich_text'][0]['plain_text'] for p in db_col]


async def update_all_homework_info_to_notion_db(homeworks: List[Dict], db: Database):
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        object_index = get_id_col(db.query())
        tasks = []
        for r in homeworks:
            if r['ID'] not in object_index:
                print(f"upload homework : {r['title']} to homework database")
                tasks.append(db.async_post(homework_in_notion_template(db, r), session))
        await asyncio.gather(*tasks)


async def update_all_bulletin_info_to_notion_db(bulletins: List[Dict], db: Database):
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        object_index = get_id_col(db.query())
        tasks = []
        for r in bulletins:
            if r['ID'] not in object_index:
                print(f"upload bulletin : {r['title']} to bulletin database")
                tasks.append(db.async_post(builtin_in_notion_template(db, r), session))
        await asyncio.gather(*tasks)

async def update_all_material_info_to_notion_db(materials: List[Dict], db: Database):
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        object_index = get_id_col(db.query())
        tasks = []
        for r in materials:
            if r != None and r['ID'] not in object_index:
                print(f"upload material : {r['title']} to material database")
                tasks.append(db.async_post(material_in_notion_template(db, r), session))
        await asyncio.gather(*tasks)
