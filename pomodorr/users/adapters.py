# from typing import Any
#
# from allauth.account.adapter import DefaultAccountAdapter
# from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
# from allauth.utils import build_absolute_uri
# from django.conf import settings
# from django.http import HttpRequest
# from django.urls import reverse
#
#
# class AccountAdapter(DefaultAccountAdapter):
#     def is_open_for_signup(self, request: HttpRequest):
#         return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)
#
#
# class SocialAccountAdapter(DefaultSocialAccountAdapter):
#     def is_open_for_signup(self, request: HttpRequest, sociallogin: Any):
#         return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)
#
#
# class CustomAccountAdapter(DefaultAccountAdapter):
#
#     def get_email_confirmation_url(self, request, emailconfirmation):
#         """Constructs the email confirmation (activation) url.
#
#         Note that if you have architected your system such that email
#         confirmations are sent outside of the request context `request`
#         can be `None` here.
#         """
#         url = reverse(
#             "account_confirm_email",
#             args=[emailconfirmation.key])
#         ret = build_absolute_uri(request=None, location=url)
#         return ret
