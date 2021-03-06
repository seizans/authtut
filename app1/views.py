# coding=utf-8
from datetime import datetime
import logging

from django.core.mail import send_mail
from django.contrib import auth
from django.shortcuts import render, render_to_response, redirect
from django.http import HttpResponseRedirect
from django.views.generic.edit import CreateView, FormView
from django.utils import timezone

import twitter

from spam.settings import FACEBOOK_ID, FACEBOOK_SECRET
from spam.settings import TWITTER_ID, TWITTER_SECRET
from .client import OAuthClient
from .forms import LoginForm, SignupForm
from .models import EmailConfirmation

FACEBOOK_AUTHORIZE_URL = 'https://www.facebook.com/dialog/oauth'
FACEBOOK_ACCESS_TOKEN_URL = 'https://graph.facebook.com/oauth/access_token'
FACEBOOK_EXPIRES_IN_KEY = 'expires'

logger = logging.getLogger('debug')


def logout(request):
    # TODO: 「ログアウトしました」をadd_messageする
    auth.logout(request)
    # TODO: nextパラメータが無かった場合にトップにリダイレクトする
    return redirect(request.GET['next'])


class LoginView(FormView):
    template_name = 'app1/login.html'
    form_class = LoginForm
    success_url = '/app1/hello'

    def form_valid(self, form):
        if self.request.GET['next']:
            self.success_url = self.request.GET['next']
        auth.login(self.request, form.user)
        return HttpResponseRedirect(self.get_success_url())


class SignupView(CreateView):
    template_name = 'app1/signup.html'
    form_class = SignupForm
    success_url = '/app1/hello'

    #TODO: form.saveからsend_confirmationまで1トランザクションにする
    def form_valid(self, form):
        def send_confirmation(request, email_confirmation):
            activate_url = '/app1/confirmation/' + email_confirmation.key
            activate_url = request.build_absolute_uri(activate_url)
            subject = '確認メールのタイトル'
            from_email = email_confirmation.email
            message = 'メール本文ここから\n\n' + activate_url + '\n\nここまで'
            recipient_list = ['shimazaki@shiguredo.jp']
            send_mail(subject, message, from_email, recipient_list)
            email_confirmation.sent = timezone.now()
            email_confirmation.save()

        self.object = form.save()
        user = self.object
        import hashlib
        import random
        bits = random.SystemRandom().getrandbits(512)
        key = hashlib.sha256(str(bits)).hexdigest()
        email_confirmation = EmailConfirmation(
            user=user, email=user.email, key=key)
        send_confirmation(self.request, email_confirmation)
        return HttpResponseRedirect(self.get_success_url())


def confirmation(request, *args, **kwargs):
    key = kwargs['key']
    if not key:
        raise RuntimeError('URLパラメータに鍵が入ってない')
    try:
        email_confirmation = EmailConfirmation.objects.get(key=key)
    except EmailConfirmation.DoesNotExist as e:
        logger.exception(e)
        #TODO: 無効なURLですページへリダイレクトする
        return redirect('/app1/hello')
    if email_confirmation.key_expired():
        logger.warning('確認URLが期限切れ')
        # TODO: URL期限切れですページへリダイレクトする
        return redirect('/app1/hello')
    if email_confirmation.verified:
        # TODO: 既に確認済みの場合に対応する
        pass
    email_confirmation.verified = True
    email_confirmation.save()
    return render_to_response('app1/hello.html')


def hello(request):
    return render(request, 'app1/hello.html')


def facebook_login(request):
    # TODO: next が無かった場合の処理
    request.session['next'] = request.GET['next']
    callback_url = request.build_absolute_uri('/app1/facebook/callback')
    redirect_url = get_redirect_url(
        FACEBOOK_AUTHORIZE_URL, FACEBOOK_ID,
        callback_url,
        '', '',
    )
    return HttpResponseRedirect(redirect_url)


def facebook_callback(request):
    callback_url = request.build_absolute_uri('/app1/facebook/callback')
    access_token = get_access_token(
        FACEBOOK_ID, callback_url,
        FACEBOOK_SECRET,  '', request.GET['code'])
    import facebook
    graph = facebook.GraphAPI(access_token['access_token'])
    profile = graph.get_object('me')
    #for x, y in profile.iteritems():
        #print x, y
    user = request.user
    if user.is_anonymous():
        print user
        raise Exception('ログインしていません')
    user.fb_token = access_token['access_token']
    user.fb_username = profile['username']
    user.fb_name = profile['name']
    user.fb_updated = datetime.now()
    user.save()
    # TODO: next が無かった場合の処理
    next = request.session.pop('next')
    return redirect(next)


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


def get_redirect_url(authorization_url, client_id, redirect_url,
                     scope, extra_params):
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
    # TODO: GETにnextパラメータが無い場合の処理
    request.session['next'] = request.GET['next']
    callback_url = request.build_absolute_uri('/app1/twitter/callback')
    #action = request.GET.get('action', 'authenticate')
    client = OAuthClient(request, TWITTER_ID, TWITTER_SECRET,
                         TWITTER_REQUEST_TOKEN_URL,
                         TWITTER_ACCESS_TOKEN_URL,
                         callback_url,
                         parameters={})
    return client.get_redirect(TWITTER_AUTHORIZE_URL)


def twitter_callback(request):
    user = request.user
    if user.is_anonymous():
        print user
        raise Exception('ログインしていません')
    callback_url = request.build_absolute_uri('/app1/twitter/callback')
    client = OAuthClient(request, TWITTER_ID, TWITTER_SECRET,
                         TWITTER_REQUEST_TOKEN_URL,
                         TWITTER_ACCESS_TOKEN_URL,
                         callback_url,
                         parameters={})
    # TODO: if not client.is_valid():
    access_token = client.get_access_token()
    token = access_token['oauth_token']
    secret = access_token['oauth_token_secret']
    api = twitter.Api(
        consumer_key=TWITTER_ID,
        consumer_secret=TWITTER_SECRET,
        access_token_key=token,
        access_token_secret=secret
    )
    tw_user = api.GetUser(access_token['user_id'])
    user.tw_token = token
    user.tw_secret = secret
    user.tw_name = tw_user.name
    user.tw_screen_name = tw_user.screen_name
    user.tw_profile_image_url = tw_user.profile_image_url
    user.tw_updated = datetime.now()
    user.save()
    next = request.session.pop('next')
    return redirect(next)


def twitter_post(token, secret):
    api = twitter.Api(
        consumer_key=TWITTER_ID,
        consumer_secret=TWITTER_SECRET,
        access_token_key=token,
        access_token_secret=secret
    )
    message = 'twitter post test'
    poststatus = api.PostUpdate(message)
    print 'POST STATUS: ', poststatus
