"""
URL configuration for social_dashboard_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from facebook_app import views
from twitter_app import urls
from twitter_app import views as v
from facebook_app import views as f
import facebook_app
import twitter_app

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls'),name='social'),
    # path('/', include(facebook_app.urls),name='social'),
    # path('/', include(twitter_app.urls),name='social'),
    path('login/',views.login_view,name='login'), 
    path('twitter/login',v.twitter_login_start),
    path('twitter_profile/',v.twitter_profile_view),
    path('post_tweet/',v.post_tweet_view,name='post_tweet'),
    path('twitter_tweets/',v.twitter_tweets_view,name='twitter_tweets'),
    path('facebook/login/',f.facebook_login_redirect) ,
    path('facebook/callback/', f.facebook_login_callback, name='facebook_login_callback'),  
    path('pages/',f.get_user_pages,name='pages'),
    path('pages/<str:page_id>',f.page_detail_view,name='page_details'),
    path("posts/<str:page_id>/",f.page_posts_view, name="page_posts"),
    path('get_comment/<str:post_id>/', f.get_comments, name='get_comments'),
    path('comment/<str:post_id>',views.add_comment_view,name='add_comment'),
    path('logout/',f.logout_view,name='logout'),
    path('signup/',f.signup_view,name='signup'),
    path('index/',f.after_login,name='index'),
     

]
