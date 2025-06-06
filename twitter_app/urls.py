
from . import views
from django.urls import path


urlpatterns = [
    path('twitter/login',views.twitter_login_start),
    path('twitter_profile/',views.twitter_profile_view),
    path('post_tweet/',views.post_tweet_view,name='post_tweet'),
    path('twitter_tweets/',views.twitter_tweets_view,name='twitter_tweets'),
]
