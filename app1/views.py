from django.views.generic import TemplateView
from django.shortcuts import render_to_response, redirect
from django.http import HttpResponseRedirect

from spam.settings import FACEBOOK_ID, FACEBOOK_SECRET
from spam.settings import TWITTER_ID, TWITTER_SECRET
from .client import OAuthClient

FACEBOOK_AUTHORIZE_URL = 'https://www.facebook.com/dialog/oauth'
FACEBOOK_ACCESS_TOKEN_URL = 'https://graph.facebook.com/oauth/access_token'
FACEBOOK_EXPIRES_IN_KEY = 'expires'


class HelloView(TemplateView):
    template_name = 'app1/hello.html'


def loginview(request):
    redirect_url = get_redirect_url(
        FACEBOOK_AUTHORIZE_URL, '', FACEBOOK_ID,
        request.build_absolute_uri('/app1/facebook/callback'),
        '',
    )
    return HttpResponseRedirect(redirect_url)


def callbackview(request):
    access_token = get_access_token(
        FACEBOOK_ID, request.build_absolute_uri('/app1/facebook/callback'),
        FACEBOOK_SECRET,  '', request.GET['code'])
    return facepost(access_token['access_token'])


def facepost(token):
    import facebook
    graph = facebook.GraphAPI(token)
    message = 'From facepost \n\n url \n hoge'
    link = 'http://docs.python.jp/2/library/index.html'
    graph.put_object('me', 'feed', message=message, link=link)
    return render_to_response('/app1/hello')


try:
    from urllib.parse import parse_qsl, urlencode  # Python3
except ImportError:
    from urllib import urlencode
    from urlparse import parse_qsl
import requests


def get_redirect_url(authorization_url, extra_params, client_id, redirect_url,
                     scope):
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_url,
        'scope': scope,
        'response_type': 'code'
    }
    params.update(extra_params)
    return '%s?%s' % (authorization_url, urlencode(params))


def get_access_token(client_id, redirect_uri, client_secret, scope, code):
    params = {'client_id': client_id,
              'redirect_uri': redirect_uri,
              'grant_type': 'authorization_code',
              'client_secret': client_secret,
              'scope': scope,
              'code': code}
    url = FACEBOOK_ACCESS_TOKEN_URL
    resp = requests.post(url, params)
    if resp.status_code == 200:
        access_token = dict(parse_qsl(resp.text))
    if not access_token or 'access_token' not in access_token:
        raise OAuth2Error('Error retrieving access token: %s'
                          % resp.content)
    return access_token


class OAuth2Error(Exception):
    pass


url = 'https://api.twitter.com/1.1/account/verify_credentials.json'
TWITTER_REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'
TWITTER_ACCESS_TOKEN_URL = 'https://api.twitter.com/oauth/access_token'
# Issue #42 -- this one authenticates over and over again...
# authorize_url = 'https://api.twitter.com/oauth/authorize'
TWITTER_AUTHORIZE_URL = 'https://api.twitter.com/oauth/authenticate'


def twitter_login(request):
    callback_url = request.build_absolute_uri('/app1/twitter/callback')
    #action = request.GET.get('action', 'authenticate')
    client = OAuthClient(request, TWITTER_ID, TWITTER_SECRET,
                         TWITTER_REQUEST_TOKEN_URL,
                         TWITTER_ACCESS_TOKEN_URL,
                         callback_url,
                         parameters={})
    return client.get_redirect(TWITTER_AUTHORIZE_URL)


def twitter_callback(request):
    callback_url = request.build_absolute_uri('/app1/twitter/callback')
    client = OAuthClient(request, TWITTER_ID, TWITTER_SECRET,
                         TWITTER_REQUEST_TOKEN_URL,
                         TWITTER_ACCESS_TOKEN_URL,
                         callback_url,
                         parameters={})
    # TODO: if not client.is_valid():
    access_token = client.get_access_token()
    print 'TOKEN: ', access_token
    return redirect('/app1/hello')
