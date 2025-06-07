from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login
from django.http import JsonResponse,HttpResponse
import requests
from allauth.socialaccount.models import SocialToken,SocialAccount
from django.contrib.auth import login,logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.core.paginator import Paginator

# Create your views here.
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None

        if user is not None:
            login(request, user)
            return redirect('index')  
        else:
            return render(request, 'login.html', {'error': 'Invalid email or password'})
    return render(request,'login.html')


@login_required(login_url='/login/')

def after_login(request):
    return render(request,'index.html')


def logout_view(request):
    logout(request)
    return redirect('login') 


def signup_view(request):
    if request.method=='POST':
        email=request.POST.get('email','')
        password=request.POST.get('password','')
        if email and password:
            user=User.objects.create_user(
                username=email,
                email=email,
                password=password
            )
            return redirect('login')
    return render(request,'signup.html')   

@login_required(login_url='/login/')

def facebook_login_redirect(request):
    fb_auth_url = (
        "https://www.facebook.com/v18.0/dialog/oauth"
        "?client_id={client_id}"
        "&redirect_uri={redirect_uri}"
        "&scope=email,public_profile,business_management"
        "&response_type=code"
    ).format(
        client_id='1777639903181938',
        redirect_uri='http://localhost:8000/facebook/callback'
    )
    return redirect(fb_auth_url)

@login_required(login_url='/login/')
def facebook_login_callback(request):
    code = request.GET.get("code")
    print(request.GET.dict())
    access_token = None
    print(code)
    print("Full GET params:", request.GET)
    code = request.GET.get("code")
    print("Code:", code)

    if code:
        token_url = "https://graph.facebook.com/v18.0/oauth/access_token"
        params = {
            "client_id": "1777639903181938",
            "redirect_uri": 'http://localhost:8000/facebook/callback',
            "client_secret": '9ea3322476e97cb26a5d3de40f4c01b2',
            "code": code
        }

        response = requests.get(token_url, params=params)
        if response.status_code == 200:
            access_token = response.json().get("access_token")
            request.session["fb_token"] = access_token
        else:
            print("Token exchange failed:", response.text)

    return render(request, "facebook_app/facebook_manage.html", {
        "access_token": access_token
    })

@login_required(login_url='/login/')
def get_user_pages(request):
    user = request.user
    # Get the Facebook SocialAccount for the logged-in user
    try:
        social_account = SocialAccount.objects.get(user=user, provider='facebook')
        user_id = social_account.uid  # Facebook User ID
        access_token=request.session.get('fb_token')
    except SocialAccount.DoesNotExist:
        return JsonResponse({"error": "Facebook account not connected"})
    except Exception as e:
        return JsonResponse({"error": f"Error: {str(e)}"})

    url = f"https://graph.facebook.com/v18.0/{user_id}/accounts"
    params = {
        "access_token": access_token
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        pages_data = response.json().get("data", [])
        #  Save page tokens in session as a dict {page_id: token}
        page_token_map = {page["id"]: page["access_token"] for page in pages_data}
        request.session["page_tokens"] = page_token_map
        return render(request,'facebook_app/pages.html',{"pages": pages_data})
    else:
        return JsonResponse({"error": response.text})
    
@login_required(login_url='/login/')   
def page_detail_view(request, page_id):
    page_tokens = request.session.get("page_tokens", {})
    page_token = page_tokens.get(page_id)

    if not page_token:
        return HttpResponse("Page access token not found.", status=403)

    fields = "name,category,fan_count,description,about,connected_instagram_account,cover"

    url = f"https://graph.facebook.com/v18.0/{page_id}"
    params = {
        "fields": fields,
        "access_token": page_token,
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        return HttpResponse(f"Error fetching page details: {response.text}", status=response.status_code)

    page_data = response.json()

    # Fetch total number of posts only
    posts_url = f"https://graph.facebook.com/v18.0/{page_id}/posts"
    posts_params = {
        "access_token": page_token,
        "summary": "true"
    }
    posts_response = requests.get(posts_url, params=posts_params)
    total_posts = 0
    if posts_response.status_code == 200:
        posts_json = posts_response.json()
        total_posts =len(posts_json['data'])
    context = {
        "page_id": page_id,
        "page_name": page_data.get("name", "N/A"),
        "page_category": page_data.get("category", "N/A"),
        "fan_count": page_data.get("fan_count", "N/A"),
        "description": page_data.get("description", "N/A"),
        "about": page_data.get("about", "N/A"),
        "connected_instagram_account": page_data.get("connected_instagram_account", {}).get("username", "Not connected"),
        "page_picture": f"https://graph.facebook.com/{page_id}/picture?type=large",
        "cover_picture": page_data.get("cover", {}).get("source", ""),
        "total_posts": total_posts,
    }
    return render(request, "facebook_app/page_details.html", context)


@login_required(login_url='/login/')
def page_posts_view(request, page_id):
    # Get page-specific access token from session
    page_tokens = request.session.get("page_tokens", {})
    access_token = page_tokens.get(page_id)

    if not access_token:
        return HttpResponseBadRequest("Page access token not found.")

    # Fetch posts using Facebook Graph API
    url = f"https://graph.facebook.com/v18.0/{page_id}/posts"
    params = {
        "access_token": access_token,
        "fields": "id,message,created_time,permalink_url,full_picture",
        "limit": 100
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        return HttpResponseBadRequest("Failed to fetch posts.")

    posts_data = response.json().get("data", [])

    # Paginate results (5 per page)
    paginator = Paginator(posts_data, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    post_ids =  page_obj.object_list
    context = {
        "page_obj": page_obj,
        "page_id": page_id,
        "post_ids": post_ids,
    }
    return render(request, "facebook_app/facebook_page_posts.html", context)

@login_required(login_url='/login/')
def get_comments(request, post_id):
    # Get access token from session 
    page_tokens = request.session.get("page_tokens", {})
    # Try to find the page ID prefix 
    page_id = post_id.split("_")[0]
    page_token = page_tokens.get(page_id)

    if not page_token:
        return HttpResponse("Page access token not found.", status=403)

    # Fetch comments
    url = f"https://graph.facebook.com/v18.0/{post_id}/comments"
    params = {
        "access_token": page_token,
        "fields": "id,message,from,created_time",
        "limit": 100  
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        return HttpResponse(f"Error fetching comments: {response.text}", status=response.status_code)

    comments = response.json().get("data", [])

    # Paginate (10 comments per page)
    paginator = Paginator(comments, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "post_id": post_id,
        "comments": page_obj,
    }
    return render(request, "facebook_app/comments_list.html", context)

@login_required(login_url='/login/')
def add_comment_view(request, post_id):
    # Extract page ID from post ID
    page_id = post_id.split("_")[0]

    # Get page access token from session
    page_tokens = request.session.get("page_tokens", {})
    page_token = page_tokens.get(page_id)

    if not page_token:
        return HttpResponse("Page access token not found.", status=403)

    if request.method == "POST":
        # Get comment text from form
        comment_text = request.POST.get("comment")

        if not comment_text:
            return HttpResponse("Comment text is required.", status=400)

        # Send comment to Facebook Graph API
        url = f"https://graph.facebook.com/v18.0/{post_id}/comments"
        params = {
            "message": comment_text,
            "access_token": page_token
        }

        response = requests.post(url, data=params)

        if response.status_code == 200:
            return HttpResponse('<h1>comment added on you post</h1>') # Redirect 1o comment list
        else:
            return HttpResponse(f"Error posting comment: {response.text}", status=response.status_code)

   
    return render(request, "facebook_app/add_comment.html", {"post_id": post_id})







    

  


