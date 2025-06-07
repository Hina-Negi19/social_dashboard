from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from allauth.socialaccount.models import SocialToken, SocialApp,SocialAccount
from requests_oauthlib import OAuth1Session
from django.shortcuts import render, redirect
from requests_oauthlib import OAuth1Session
import tweepy
from django.http import JsonResponse
import requests
from django.conf import settings


@login_required(login_url='/login/')   
def twitter_profile_view(request):
    user = request.user

    try:
        token_obj = SocialToken.objects.get(account__user=user, account__provider='twitter')
        app = SocialApp.objects.get(provider='twitter')
    except SocialToken.DoesNotExist:
        return render(request, "error.html", {"message": "Twitter token not found."})
    except SocialApp.DoesNotExist:
        return render(request, "error.html", {"message": "Twitter app not configured in admin."})

    twitter = OAuth1Session(
        client_key=app.client_id,                 # Fetched from SocialApp
        client_secret=app.secret,                # Fetched from SocialApp
        resource_owner_key=token_obj.token,      # User's token
        resource_owner_secret=token_obj.token_secret,  # User's token secret
    )

    response = twitter.get("https://api.twitter.com/1.1/account/verify_credentials.json")

    if response.status_code != 200:
        return render(request, "error.html", {"message": "Failed to fetch profile.", "details": response.text})

    return render(request, "twitter_app/twitter_profile.html", {"profile": response.json()})


from allauth.socialaccount.models import SocialApp
from tweepy import OAuth1UserHandler
from django.shortcuts import redirect
from django.http import HttpResponse

@login_required(login_url='/login/')   
def twitter_login_start(request):
    # Get Twitter app credentials from the SocialApp model
    try:
        app = SocialApp.objects.get(provider='twitter')
    except SocialApp.DoesNotExist:
        return HttpResponse("Twitter SocialApp not configured.")

    consumer_key = app.client_id
    consumer_secret = app.secret

    # Initialize Tweepy OAuth flow
    auth = OAuth1UserHandler(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        callback='http://localhost:8000/accounts/twitter/login/callback/'  # Match with Twitter App settings
    )

    try:
        
        redirect_url = auth.get_authorization_url()
        request.session['request_token'] = auth.request_token

        # Redirect user to Twitter login page
        return redirect(redirect_url)

    except Exception as e:
        return HttpResponse(f"Error initiating Twitter login: {e}")
    
    
def get_tweepy_client(user):
    token = SocialToken.objects.get(account__user=user, account__provider='twitter')
    app = SocialApp.objects.get(provider='twitter')

    client = tweepy.Client(
        consumer_key=app.client_id,
        consumer_secret=app.secret,
        access_token=token.token,
        access_token_secret=token.token_secret
    )
    return client    


def post_tweet_view(request):
    if request.method == 'POST':
        tweet_text = request.POST.get('tweet_text')
        client = get_tweepy_client(request.user)
        response = client.create_tweet(text=tweet_text)  # API v2 endpoint
        if response and response.data:
            return JsonResponse({'msg': 'success', 'tweet_id': response.data['id']})
        else:
            return JsonResponse({'msg': 'failed'}, status=400)
    return render(request, 'twitter_app/post_tweet.html')


@login_required(login_url='/login/')   

def twitter_tweets_view(request):
    bearer_token = getattr(settings, 'TWITTER_BEARER_TOKEN', None)

    if not bearer_token:
        return JsonResponse({"error": "Bearer token not configured."}, status=400)

    username = "HinaNegi19"  
    user_url = f"https://api.twitter.com/2/users/by/username/{username}"
    headers = {
        "Authorization": f"Bearer {bearer_token}"
    }
    user_resp = requests.get(user_url, headers=headers)
    if user_resp.status_code != 200:
          return render(request,'twitter_app/error.html')

    user_data = user_resp.json()
    user_id = user_data.get("data", {}).get("id")
    if not user_id:
        return JsonResponse({"error": "User ID not found in response"}, status=400)

    # Step 2: Get tweets by user ID
    
    tweets_url = f"https://api.twitter.com/2/users/{user_id}/tweets"

    params = {
        "max_results": 10,
        "tweet.fields": "created_at,text,public_metrics"
    }
    tweets_resp = requests.get(tweets_url, headers=headers, params=params)

    if tweets_resp.status_code != 200:
        return JsonResponse({
            "error": "Failed to fetch tweets",
            "status_code": tweets_resp.status_code,
            "details": tweets_resp.text
        }, status=tweets_resp.status_code)
   
    tweets_data = tweets_resp.json().get("data", [])
    return render(request, 'twitter_app/twitter_tweets.html', {"tweets": tweets_data})
