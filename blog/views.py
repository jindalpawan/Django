from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from .models import Post, Comment
from django.views.generic import TemplateView, DetailView
from .forms import NewpostForm, SignupForm, EditProfileForm, EditPasswordForm, CommentForm
from django.utils import timezone
from datetime import datetime
import urllib3
import json
import random
import hashlib
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth import logout, login, authenticate
import os



class HomePage(TemplateView):
	def get(self, request):
		posts= Post.objects.all().order_by('create_date').reverse()
		return render(request, 'blog/front.html', {'alldata':posts})


class NewPost(TemplateView):
	def get(self,request):
		bg=NewpostForm(request.GET)
		user=None
		user=request.user
		if user.is_authenticated:
			return render(request,"blog/newpost.html",{'user':user})
		else:
			return redirect(reverse('blog:signup',))

	def post(self, request):
		bg=NewpostForm(request.POST)
		if bg.is_valid():
			author=request.user
			title= bg.cleaned_data['title']
			content=bg.cleaned_data['content']
			content=content.replace('\n', '<br>')
			p=Post(title= title, content=content,author= author)
			p.save()
			return redirect(reverse('blog:onepost',args=(p.pk,)))
		else:
			title= bg.cleaned_data['title']
			content=bg.cleaned_data['content']
			return render(request, 'blog/newpost.html',{'title': title, 'content':content})


class Perma(TemplateView):
	def get(self,request, pk):
		post= Post.objects.filter(pk=pk).first()
		cmnts=Comment.objects.filter(post=post).first()
		if cmnts:
			cmnts=True
		user=request.user
		if user.is_authenticated:
			like=post.likes.filter(id=user.id).first()
			if like:
				like="Unlike"
			else:
				like="Like"
			
			delete=False
			if user==post.author:
				delete=True
			return render(request, "blog/perma.html",{'post':post,'cmnts':cmnts, 'like':like, 'delete': delete})
		else:
			return render(request, "blog/perma.html",{'post':post})


class PostDelete(TemplateView):
	def get(self,request, pk):
		post= Post.objects.filter(pk=pk).first()
		user=request.user
		if user.is_authenticated and user==post.author:
			post.delete()
		return redirect(reverse('blog:home',))
		
	

@csrf_exempt
def comments(request):
	if request.method== 'POST':
		user=None
		user=request.user
		if user.is_authenticated:
			postid=request.POST['postid']
			msg=request.POST['msg']
			if len(msg)>0:
				post= Post.objects.filter(pk=postid).first()
				cmt=Comment(user=user,post=post,msg=msg)
				cmt.save()
			response={'reply':1,}
			return JsonResponse(response,)
		response={'reply':0,}
		return JsonResponse(response,)


@csrf_exempt
def PostLike(request):
	if request.method== 'POST':
		user=request.user
		if user.is_authenticated:
			postid=request.POST['post_id']
			post= Post.objects.filter(pk=postid).first()
			if post.likes.filter(id=user.id).first():
				post.likes.remove(user)
				msg="Like"
			else:	
				post.likes.add(user)
				msg="Unlike"
			response={'like_count': post.total_likes(), 'msg':msg,}
			return JsonResponse(response,)
		response={}
		return JsonResponse(response,)


def AllComments(request):
	if request.method== 'GET':
		postid=request.GET['postid']
		post=Post.objects.filter(id=postid).first()
		allcmnts= Comment.objects.filter(post=post)
		alldata=[]
		for cmnt in allcmnts:
			x=[]
			s=cmnt.user.first_name
			s=s+" " + cmnt.user.last_name
			x.append(s)
			x.append(cmnt.msg)
			alldata.append(x)
		return JsonResponse(alldata,safe=False)


class Profile(TemplateView):
	def get(self,request):
		user=None
		user=request.user
		if user.is_authenticated:
			posts=Post.objects.filter(author=user.id)
			return render(request, "blog/profile.html",{'user':user,'posts':posts})
		else:
			return redirect(reverse('blog:signup',))


class EditProfile(TemplateView):
	def get(self,request):
		sig=EditProfileForm(request.GET)
		user=None
		user=request.user
		dic={}
		if user.is_authenticated:
			dic['username']=user.username
			dic['email']=user.email
			dic['first_name']=user.first_name
			dic['last_name']=user.last_name
			return render(request,"blog/edit_profile.html",dic)
		else:
			return redirect(reverse('blog:signup',))

	def post(self, request):
		user=request.user
		sig=EditProfileForm(request.POST, instance=user)
		if sig.is_valid():
			username=sig.cleaned_data['username']
			first_name=sig.cleaned_data['first_name']
			last_name=sig.cleaned_data['last_name']
			email=sig.cleaned_data['email']
			user=request.user
			if user.is_authenticated:
				user.username=username
				user.first_name= first_name
				user.last_name= last_name
				user.email=email
				user.save()
			return redirect(reverse('blog:profile',))
		
		else:
			return render(request,"blog/edit_profile.html",)	


class EditPassword(TemplateView):
	def get(self,request):
		sig=EditPasswordForm(request.GET)
		user=None
		user=request.user
		dic={}
		if user.is_authenticated:
			return render(request,"blog/edit_pass.html",)
		else:
			return redirect(reverse('blog:signup',))

	def post(self, request):
		user=request.user
		sig=EditPasswordForm(request.POST, instance=user)
		if sig.is_valid():
			user=request.user
			password=sig.cleaned_data['password']
			newpass=sig.cleaned_data['newpass']
			vpass=sig.cleaned_data['vpass']
			dic={}
			if user.password!=password:
				dic['error_password']="Wrong Password!!!!!!"
			if newpass!= vpass:
				dic['error_vpass']="Password not match!!!!!!"
			
			if not dic:
				user.password=newpass
				user.save()
				return redirect(reverse('blog:profile',))
			else:
				return render(request,'blog/edit_pass.html',dic)
			
		else:
			return render(request,'blog/edit_pass.html',)	



fbid = os.environ.get('fbid')

class Login(TemplateView):
	def get(self, request):
		logout(request)
		return render(request,"blog/login.html",{'id':fbid})

	def post(self, request):
		username= request.POST['username']
		password= request.POST['password']
		user = authenticate(username=username, password=password)
		if user is not None:
			login(request, user)
			return redirect(reverse('blog:home',))
		else:
			dic={'username':username,'error_password':"Username or Password not matcheds"}
			return render(request,"blog/login.html",dic)


class Signup(TemplateView):
	def get(self,request):
		sig=SignupForm(request.GET)
		logout(request)
		return render(request,"blog/signup.html",{'id':fbid})

	def post(self, request):
		sig=SignupForm(request.POST)
		if sig.is_valid():
			username= sig.cleaned_data['username']
			first_name=sig.cleaned_data['first_name']
			last_name=sig.cleaned_data['last_name']
			email=sig.cleaned_data['email']
			password=sig.cleaned_data['password']
			vpass=sig.cleaned_data['vpass']
			dic={}
			if password != vpass:
				dic['error_vpass']="Password not matched"
			if (User.objects.filter(username=username).first()):
				dic['error_username']="This username already exist"
			if (User.objects.filter(email=email).first()):
				dic['error_email']="This email already exist"

			if dic:
				dic['username']=username
				dic['first_name']=first_name
				dic['last_name']=last_name
				dic['email']=email
				return render(request,'blog/signup.html',dic)
			else:
				p=User.objects.create_user(username=username, first_name=first_name,last_name=last_name, email= email, password=password)
				login(request, p)
				return redirect(reverse('blog:home',))
		else:
			return render(request,'blog/signup.html',)	


class FacebookData(TemplateView):
	def get(self, request):
		fbscurekey= os.environ.get('fbscurekey')
		URL= 'https://graph.facebook.com/v6.0/oauth/access_token?client_id=%s&redirect_uri=https://uploadsomethinks.herokuapp.com/dataa&client_secret=%s&code='%(fbid,fbscurekey)
		URL2="https://graph.facebook.com/me?access_token="
		code=request.GET['code']
		code=URL+str(code)
		lib = urllib3.PoolManager()
		r = lib.request('GET', code)
		data=json.loads(r.data.decode('utf-8'))
		token= str(data["access_token"])
		URL2= URL2+(token)+"&fields=id,name"
		rr= lib.request('GET', URL2)
		data2= json.loads(rr.data.decode('utf-8'))
		username= str(data2['id'])
		if not username:
			return redirect(reverse('blog:signup',))
		name= str(data2['name'])
		password=username
		obj= User.objects.filter(username=username).first()
		if not obj:
			name=list(name.split(' '))
			obj= User.objects.create_user(username=username, first_name=name[0],last_name=name[1], email="", password=password)
		login(request, obj)
		return redirect(reverse('blog:home',))
