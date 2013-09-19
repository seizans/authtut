# coding=utf-8
from django.views.generic import TemplateView
from django.shortcuts import render_to_response, redirect
from django.http import HttpResponseRedirect
from django.views.generic.edit import CreateView, ModelFormMixin

import twitter

from spam.settings import FACEBOOK_ID, FACEBOOK_SECRET
from spam.settings import TWITTER_ID, TWITTER_SECRET
from .client import OAuthClient
from .forms import SignupForm
from .models import EmailConfirmation

FACEBOOK_AUTHORIZE_URL = 'https://www.facebook.com/dialog/oauth'
FACEBOOK_ACCESS_TOKEN_URL = 'https://graph.facebook.com/oauth/access_token'
FACEBOOK_EXPIRES_IN_KEY = 'expires'


class SignupView(CreateView):
    template_name = 'app1/signup.html'
    form_class = SignupForm
    success_url = '/app1/hello'

    #TODO: form.saveからsend_confirmationまで1トランザクションにする
    def form_valid(self, form):
        self.object = form.save()
        user = self.object
        import hashlib
        import random
        bits = random.SystemRandom().getrandbits(512)
        key = hashlib.sha256(str(bits)).hexdigest()
        email_confirmation = EmailConfirmation(
            user=user, email=user.email, key=key)
        email_confirmation.send_confirmation(self.request)
        return super(ModelFormMixin, self).form_valid(form)


class ConfirmationView(TemplateView):
    def get(self, *args, **kwargs):
        key = kwargs['key']
        if not key:
            raise RuntimeError('URLパラメータに鍵が入ってない')
        confirmation = EmailConfirmation.objects.get(key=key)
        # TODO: confirmation が引けなかった場合の対応を書く
        if confirmation.key_expired():
            # TODO: URL期限切れの場合に対応する
            raise RuntimeError('確認URLが期限切れ')
        if confirmation.verified:
            # TODO: 既に確認済みの場合に対応する
            pass
        confirmation.verified = True
        confirmation.save()
        return render_to_response('app1/hello.html')


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
    print 'TOKEN: ', access_token['oauth_token_secret']
    token = access_token['oauth_token']
    secret = access_token['oauth_token_secret']
    api = twitter.Api(
        consumer_key=TWITTER_ID,
        consumer_secret=TWITTER_SECRET,
        access_token_key=token,
        access_token_secret=secret
    )
    message = 'twitter post test'
    poststatus = api.PostUpdate(message)
    print 'POST STATUS: ', poststatus
    return redirect('/app1/hello')
