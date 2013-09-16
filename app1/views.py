from django.views.generic import TemplateView
from django.shortcuts import redirect, render_to_response
from django.http import HttpResponseRedirect

#from requests_oauthlib import OAuth2Session
#from requests_oauthlib.compliance_fixes.facebook import facebook_compliance_fix

from spam.settings import FACEBOOK_ID, FACEBOOK_SECRET


class HelloView(TemplateView):
    print FACEBOOK_ID
    template_name = 'app1/hello.html'


def loginview(request):
    fb = OAuth2Client(request, FACEBOOK_ID, FACEBOOK_SECRET,
                      FACEBOOK_ACCESS_TOKEN_URL,
                      request.build_absolute_uri('/app1/facebook/callback'),
                      '')
    redirect_url = fb.get_redirect_url(FACEBOOK_AUTHORIZE_URL, '')
    print redirect_url
    return HttpResponseRedirect(redirect_url)


FACEBOOK_AUTHORIZE_URL = 'https://www.facebook.com/dialog/oauth'
FACEBOOK_ACCESS_TOKEN_URL = 'https://graph.facebook.com/oauth/access_token'
FACEBOOK_EXPIRES_IN_KEY = 'expires'


def facepost(token):
    import facebook
    graph = facebook.GraphAPI(token)
    message = 'From facepost \n\n url \n hoge'
    link = 'http://docs.python.jp/2/library/index.html'
    graph.put_object('me', 'feed', message=message, link=link)
    return render_to_response('/app1/hello')


def callbackview(request):
    fb = OAuth2Client(request, FACEBOOK_ID, FACEBOOK_SECRET,
                      FACEBOOK_ACCESS_TOKEN_URL,
                      request.build_absolute_uri('/app1/facebook/callback'),
                      '')
    print 'CODE: ', request.GET['code']
    access_token = fb.get_access_token(request.GET['code'])
    print access_token
    return facepost(access_token['access_token'])


try:
    from urllib.parse import parse_qsl, urlencode
except ImportError:
    from urllib import urlencode
    from urlparse import parse_qsl
import requests


class OAuth2Error(Exception):
    pass


class OAuth2Client(object):

    def __init__(self, request, consumer_key, consumer_secret,
                 access_token_url,
                 callback_url,
                 scope):
        self.request = request
        self.access_token_url = access_token_url
        self.callback_url = callback_url
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.scope = ' '.join(scope)
        self.state = None

    def get_redirect_url(self, authorization_url, extra_params):
        params = {
            'client_id': self.consumer_key,
            'redirect_uri': self.callback_url,
            'scope': self.scope,
            'response_type': 'code'
        }
        if self.state:
            params['state'] = self.state
        params.update(extra_params)
        return '%s?%s' % (authorization_url, urlencode(params))

    def get_access_token(self, code):
        params = {'client_id': self.consumer_key,
                  'redirect_uri': self.callback_url,
                  'grant_type': 'authorization_code',
                  'client_secret': self.consumer_secret,
                  'scope': self.scope,
                  'code': code}
        url = self.access_token_url
        # TODO: Proper exception handling
        resp = requests.post(url, params)
        access_token = None
        if resp.status_code == 200:
            # Weibo sends json via 'text/plain;charset=UTF-8'
            if (resp.headers['content-type'].split(';')[0] == 'application/json'
                or resp.text[:2] == '{"'):
                access_token = resp.json()
            else:
                access_token = dict(parse_qsl(resp.text))
        if not access_token or 'access_token' not in access_token:
            raise OAuth2Error('Error retrieving access token: %s'
                              % resp.content)
        return access_token


"""
def loginview2(request):
    oauth = OAuth2Session(FACEBOOK_ID,
                          redirect_uri='http://local-test.com:8000/app1/hello')
    facebook = facebook_compliance_fix(oauth)
    #authorization_response, state = facebook.authorization_url(
        #FACEBOOK_AUTHORIZE_URL)
    authorization_url, state = facebook.authorization_url(
        FACEBOOK_AUTHORIZE_URL)
    print 'Go here and authorize,', authorization_url
    authorization_response = raw_input('Enter the full callback URL')
    #import requests
    #authorization_response = requests.post(authorization_url)
    token = facebook.fetch_token(
        FACEBOOK_ACCESS_TOKEN_URL,
        authorization_response=authorization_response,
        client_secret=FACEBOOK_SECRET)
    print 'token = ', token
    return redirect(HelloView)
"""
