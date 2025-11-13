import json
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .models import User, Post, Follow, Like
from django.core.paginator import Paginator


def index(request):
    allPosts = Post.objects.all().order_by("id").reverse()

    paginator = Paginator(allPosts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "network/index.html", {
        "allPosts": allPosts,
        "page_obj": page_obj
    })

def edit(request, post_id):
    if request.method == "POST":
        data = json.loads(request.body)
        editPost = Post.objects.get(pk=post_id)
        editPost.content = data["content"]
        editPost.save()
        return JsonResponse({"message": "Post updated successfully!", "data": data["content"]})

def toggle_like(request, post_id):
    if request.user.is_authenticated:
        post = Post.objects.get(id=post_id)
        existing_like = Like.objects.filter(user=request.user, post=post).first()
        
        if existing_like:
            existing_like.delete()
            action = "unliked"
        else:
            Like.objects.create(user=request.user, post=post)
            action = "liked"
        
        like_count = post.users_liked.count()
        
        return JsonResponse({
            "success": True,
            "like_count": like_count,
            "action": action,
        })
    return JsonResponse({"success": False, "message": "User not authenticated"})

def newPost(request):
    if request.method == "POST":
        content = request.POST['content']
        user = User.objects.get(pk=request.user.id)
        post = Post(content=content, user=user)
        post.save()
        return redirect(reverse("index"))
    return render(request, "network/newPost.html")
    


def profile(request, user_id):
    profile_user = get_object_or_404(User, pk=user_id)  
    logged_in_user = request.user
    userPosts = Post.objects.filter(user=profile_user).order_by("id").reverse()

    following = profile_user.following.all()
    followers = profile_user.followers.all()

    is_following = Follow.objects.filter(follower=logged_in_user, followed=profile_user).exists()

    paginator = Paginator(userPosts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "network/profile.html", {
        "profile_user":profile_user,
        "logged_in_user": logged_in_user,
        "userPosts": userPosts,
        "page_obj": page_obj,
        "username": profile_user.username,
        "following": following,
        "followers": followers,
        "is_following": is_following
    })


def following(request):
    user = request.user
    following_users = [follow.followed for follow in user.following.all()]
    posts = Post.objects.filter(user__in=following_users).order_by("-date")

    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "network/following.html", {
        "page_obj": page_obj
    })




def follow(request):
    follower = request.user
    followed_username = request.POST['userfollow']
    followed = get_object_or_404(User, username=followed_username)
    f = Follow(follower=follower, followed=followed)
    f.save()

    return redirect("profile", user_id=followed.id)

def unfollow(request):
    follower = request.user
    followed_username = request.POST['userfollow']
    followed = get_object_or_404(User, username=followed_username)
    f = Follow.objects.filter(follower=follower, followed=followed).first()
    if f:
      f.delete()

    return redirect("profile", user_id=followed.id)

def login_view(request):
    if request.method == "POST":

        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")
