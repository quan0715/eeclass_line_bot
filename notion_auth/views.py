from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from django.views import View
import requests as re
from oauthlib.oauth2 import WebApplicationClient

from eeclass_line_bot.views import *
from notion_auth.apps import NotionAuthConfig
import json
import base64
from django.conf import settings
from requests.auth import HTTPBasicAuth

# Create your views here.

server_url = 'quan.squidspirit.com'  # The URL of this server
redirect_uri = f"https://{server_url}/notion/redirect/"


def notion_auth_start(request, state):
    # print(user_id)
    client_id = settings.NOTION_OAUTH_CLIENT_ID
    print(client_id)
    authorization_base_url = "https://api.notion.com/v1/oauth/authorize"
    client = WebApplicationClient(settings.NOTION_OAUTH_CLIENT_ID, state=state)
    # print(authorization_base_url)
    # print(client.prepare_request_uri(authorization_base_url, redirect_uri))
    # request.session['user_id'] = user_id
    # authorize_request_url = client.prepare_request_uri(authorization_base_url, redirect_uri)
    # print(client.prepare_request_uri(authorization_base_url, redirect_uri=redirect_uri, state=state))
    return redirect(client.prepare_request_uri(authorization_base_url, redirect_uri=redirect_uri, state=state))
    # return redirect(f"{authorization_base_url}?client_id={client_id}&state={state}&response_type=code&owner=user&redirect_uri={redirect_uri}")


def notion_auth_callback(request):
    # print(state)
    token_url = "https://api.notion.com/v1/oauth/token"
    url = "https://quan.squidspirit.com" + request.get_full_path()
    print(f"url: {url}")
    # print(request.session.get['user_id'])
    client = WebApplicationClient(settings.NOTION_OAUTH_CLIENT_ID)
    uri_request = (client.parse_request_uri_response(url))  # Extracts the code from the url
    state = uri_request['state']
    user_id = cache.get(state)
    token_request_params = client.prepare_token_request(token_url, url, redirect_uri, state=state)
    print(token_request_params)
    #state = token_request_params[1]
    # print(cache.get(state))
    # print(token_request_params)
    # Makes a request for the token, authenticated with the client ID and secret
    auth = HTTPBasicAuth(
        settings.NOTION_OAUTH_CLIENT_ID, settings.NOTION_OAUTH_SECRET_KEY)
    # authorization_code = f"{settings.NOTION_OAUTH_CLIENT_ID}:{settings.NOTION_OAUTH_SECRET_KEY}"
    # auth = base64.b64encode(authorization_code.encode('ascii'))
    # headers = {
    #     "Accept": "application/json",
    #     'Authorization' : f'Bearer {settings.NOTION_OAUTH_SECRET_KEY}',
    #     'Content-Type' : 'application/json',
    #     'Notion-Version' : '2022-06-28'
    # }
    print(auth)
    print(token_request_params[2])
    response = re.post(token_request_params[0], headers=token_request_params[1], data=token_request_params[2], auth=auth)
    # body = {
    #     'grant_type':'authorization_code',
    #     'client_id': settings.NOTION_OAUTH_CLIENT_ID,
    #     'redirect_uri':redirect_uri,
    #     'code':uri_request['code']
    # }
    # response = re.post(token_request_params[0], headers=headers, json=body)
    data = response.json()
    #print(response.request.body)
    print(data)
    # try:
    #TODO should check use exist or not?
    user = LineUser.objects.get(line_user_id=user_id)

    user.notion_token = data['access_token']
    user.eeclass_db_id = data['duplicated_template_id']
    user.save()
    LineBotCallbackView.update_auth_token(user_id=user_id)
    # return redirect("https://line.me/R/ti/p/%4https://line.me0085coegp")
    return HttpResponse('<a href="https://line.me/R/@0085coegp/next">連線成功點我返回聊天室 </a>')

