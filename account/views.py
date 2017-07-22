from django.shortcuts import render
from django.views.generic import View, FormView
from django.contrib.auth.models import User
from .models import UserExt
from .forms import RegisterForm, LoginForm, ResetPasswordForm, ResetPasswordConfirmForm
from django.utils import timezone
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
import datetime
from django.core.mail import send_mail
from django.urls import reverse
# from shopping import settings
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout

import json


class ReisterView(View):

    def post(self, request, *args, **kwargs):
        form = RegisterForm(request.POST)
        return self._register(form)

    def get(self, request, *args, **kwargs):
        form = RegisterForm(request.GET)
        return self._register(form)

    def _register(self, form):
        if form.is_valid():
            username = form.cleaned_data.get('username', '')
            password = form.cleaned_data.get('password', '')
            email = form.cleaned_data.get('email', '')
            try:
                with transaction.atomic():
                    user = User.objects.create_user(username=username, password=password, email=email)
                    validkey = UserExt.gen_validkey()
                    user_ext = UserExt.objects.create(user=user, realname='', birthday=datetime.date(1945, 1, 1),\
                                                      nickname='', avatar='default', telephone='', logintime=timezone.now(),
                                                      validkey=validkey)
                    content = '欢迎注册[小智的商城], 请点击此处进行激活用户: http://192.168.10.220:8888/account/active/?username=' \
                               '{username}&validkey={validkey}'.format(username=username, validkey=validkey)
                    send_mail('Userregister', content, settings.EMAIL_HOST_USER, [email])
            except BaseException as e:
                return JsonResponse({'status': 500})

            return JsonResponse({'status': 200})
        else:
            return JsonResponse({'status': 400, 'errors': json.loads(form.errors.as_json()), 'result': ''})


class ActiveView(View):

    # def get(self, request, *args, **kwargs):
    #     username = request.GET.get('username', '')
    #     validkey = request.GET.get('validkey', '')
    #
    #     try:
    #         user = User.objects.get(username=username)
    #         if user.userext.status == 0 and user.userext.validkey != '':
    #             if user.userext.validkey == validkey:
    #                 user.userext.status = 1
    #                 user.userext.save()
    #                 return HttpResponse("激活成功")
    #             else:
    #                 return HttpResponse("验证码不正确")
    #
    #         return HttpResponse("用户已经激活")
    #
    #     except ObjectDoesNotExist as e:
    #         pass
    #     return HttpResponse("用户不存在")
    def get(self, request, *args, **kwargs):
        username = request.GET.get('username', '')
        validkey = request.GET.get('validkey', '')

        # objectdoesnotexists
        try:
            user = User.objects.get(username=username)
            if user.userext.status == 0 and user.userext.validkey != '':
                if user.userext.validkey == validkey:
                    user.userext.status = 1
                    user.userext.validkey = ''
                    user.userext.save()
                    messages.add_message(request, messages.INFO, '激活成功, 请登录')
                else:
                    messages.add_message(request, messages.ERROR, '激活失败, 用户名或验证码不正确')
            else:
                messages.add_message(request, messages.ERROR, '激活失败, 用户名或验证码不正确')
        except ObjectDoesNotExist as e:
            messages.add_message(request, messages.ERROR, '激活失败, 用户名或验证码不正确')
            # 跳转到页面\

        return HttpResponseRedirect(reverse('index'))


# class LoginView(View):
#     def post(self, request, *args, **kwargs):
#         form = LoginForm(request.POST)
#         if form.is_valid():
#             login(request, form.cached_user)
#             return JsonResponse({'status': 200, 'errors': {}, 'result': {}})
#         else:
#             return JsonResponse({'status': 400, 'errors': {'default': [{'message': '用户名或者密码错误'}]}},)


class LoginView(FormView):
    form_class = LoginForm

    #验证成功
    def form_valid(self, form):
        login(self.request, form.cached_user)
        return JsonResponse({'status': 200, 'errors': {}, 'result': {}})

    ##验证失败
    def form_invalid(self, form):
        return JsonResponse({'status': 400, 'errors': {'default': [{'message': '用户名或者密码错误'}]}}, )

class ModifyPasswordView(View):
    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return HttpResponse("success")
        else:
            return HttpResponse("fail")


class LogoutView(View):
    def get(self, request, *args, **kwargs):
            logout(request)
            return HttpResponseRedirect(reverse("index"))


class ResetPasswordView(FormView):
    template_name = 'account/reset_password.html'
    form_class = ResetPasswordForm

    def form_valid(self, form):
        try:
            with transaction.atomic():
                user = form.cached_user
                validkey = user.userext.gen_validkey()
                user.userext.validkey = validkey
                user.userext.save()
                content = '欢迎注册[小智的商城], 请点击此处进行重置用户: http://192.168.10.220:8888/account/reset_password_confirm/?username=' \
                          '{username}&validkey={validkey}'.format(username=user.username, validkey=validkey)
                send_mail('Userregister', content, settings.EMAIL_HOST_USER, [user.email])

                messages.add_message(self.request, messages.INFO, '重置密码邮件已经发送，请查收邮件进行密码重置')
        except BaseException as e:
            messages.add_message(self.request, messages.ERROR, '重置密码邮件发送失败，请重试')
        return HttpResponseRedirect(reverse("index"))

    def form_invalid(self, form):
        return render(self.request, self.template_name, {'form': form})


class ResetPasswordConfirmView(FormView):
    template_name = "account/reset_password_confirm.html"
    form_class = ResetPasswordConfirmForm

    def get_initial(self):
        return self.request.GET

    def form_valid(self, form):
        user = form.cached_user
        password = form.cleaned_data.get('password', '')
        user.set_password(password)
        user.save()
        user.userext.validkey = ''
        user.save()
        messages.add_message(self.request, messages.INFO, '重置密码成功，请重新登录')
        return HttpResponseRedirect(reverse('index'))

    def form_invalid(self, form):
        return render(self.request, self.template_name, {'form': form})

