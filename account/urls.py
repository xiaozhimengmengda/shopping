from django.conf.urls import url
from .views import ReisterView, ActiveView, LoginView, LogoutView, ResetPasswordView, ResetPasswordConfirmView
app_name = "account"

urlpatterns = [
    url(r'^register/', ReisterView.as_view(), name='register'),
    url(r'^active/', ActiveView.as_view(), name='active'),
    url(r'^login/', LoginView.as_view(), name="login"),
    url(r'^logout/', LogoutView.as_view(), name="logout"),
    url(r'^reset_password/', ResetPasswordView.as_view(), name="reset_password"),
    url(r'^reset_password_confirm/', ResetPasswordConfirmView.as_view(), name="reset_password_confirm"),
]
