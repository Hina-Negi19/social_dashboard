from django.urls import path
from . import views
urlpatterns=[
    path('facebook/login/',views.facebook_login_redirect) ,
    path('facebook/callback/', views.facebook_login_callback, name='viewsacebook_login_callback'),  
    path('pages/',views.get_user_pages,name='pages'),
    path('pages/<str:page_id>',views.page_detail_view,name='page_details'),
    path("posts/<str:page_id>/",views.page_posts_view, name="page_posts"),
    path('get_comment/<str:post_id>/', views.get_comments, name='get_comments'),
    path('comment/<str:post_id>',views.add_comment_view,name='add_comment'),
    path('logout/',views.logout_view,name='logout'),
    path('signup/',views.signup_view,name='signup'),
    path('index/',views.after_login,name='index'),
]