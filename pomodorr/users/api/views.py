# from django.contrib.auth import get_user_model
# from rest_framework import permissions, status
# from rest_framework.decorators import action
# from rest_framework.generics import get_object_or_404, RetrieveUpdateDestroyAPIView, ListCreateAPIView
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
#
# from .permissions import IsObjectOwner, IsNotAuthenticated
# from .serializers import UserCreateSerializer, UserBasicSerializer, EmailSerializer, PasswordResetSerializer, \
#     PasswordChangeSerializer, EmailChangeSerializer, UserDetailSerializer
#
# from django.utils.translation import gettext_lazy as _
#
# from pomodorr.users.services import UserDomainModel
# from pomodorr.tools.utils import PermissionMixin, account_activation_token, password_reset_token, \
#     email_address_change_token
#
# User = get_user_model()
#
#
# class UserViewSet(PermissionMixin, RetrieveUpdateDestroyAPIView):
#     http_method_names = ("get", "patch", "delete", "post")
#
#     queryset = UserDomainModel.get_active_standard_users()
#     permission_classes_by_action = {'retrieve': (IsAuthenticated, IsObjectOwner),
#                                     'partial_update': (IsAuthenticated, IsObjectOwner),
#                                     'destroy': (IsAuthenticated, IsObjectOwner)}
#
#     def get_serializer_class(self):
#         if self.request.method in permissions.SAFE_METHODS or self.request.method == "PATCH":
#             return UserDetailSerializer
#         return UserBasicSerializer
#
#     @action(detail=True, methods=['get'], url_path='activate-account/(?P<token>[^/w]+)',
#             permission_classes=(IsNotAuthenticated,))
#     def activate_account(self, request, pk, token):
#         if token is not None:
#             user = get_object_or_404(UserDomainModel.get_non_active_standard_users(), pk=pk)
#             if account_activation_token.check_token(user=user, token=token):
#                 UserDomainModel.activate_user(user_object=user)
#                 return Response(status=status.HTTP_200_OK, data={"detail": _("Account has been activated.")})
#         return Response(status=status.HTTP_404_NOT_FOUND, data={"detail": _("The link is invalid.")})
#
#     @action(detail=False, methods=["get"], permission_classes=(permissions.IsAuthenticated,))
#     def request_password_change(self, request):
#         UserDomainModel.send_password_change_mail(user_object=request.user)
#         return Response(status=status.HTTP_202_ACCEPTED,
#                         data={"detail": _("An email with password change link has been sent.\n "
#                                           "The link will be valid for one day.")})
#
#     @action(detail=True, methods=['post'], url_path='change-password/(?P<token>[^/w]+)',
#             permission_classes=(permissions.IsAuthenticated, IsObjectOwner))
#     def change_password(self, request, pk, token):
#         if token:
#             user = get_object_or_404(self.queryset, pk=pk)
#             self.check_object_permissions(request, user)
#             if password_reset_token.check_token(user=user, token=token):
#                 password_change_serializer = PasswordChangeSerializer(user=user, data=request.data)
#
#                 if password_change_serializer.is_valid(raise_exception=True):
#                     UserDomainModel.set_new_password(user_object=user,
#                                                      new_password=password_change_serializer.validated_data.get(
#                                                          "password"))
#                     return Response(status=status.HTTP_200_OK, data={"detail": _("The password has been changed.")})
#
#         return Response(status=status.HTTP_404_NOT_FOUND, data={"detail": _("The link is invalid.")})
#
#     @action(detail=False, methods=['post'], permission_classes=(IsNotAuthenticated,))
#     def request_password_reset(self, request):
#         email_serializer = EmailSerializer(data=request.data)
#
#         if email_serializer.is_valid(raise_exception=True):
#             user = get_object_or_404(self.queryset, email=email_serializer.validated_data.get("email"))
#             UserDomainModel.send_password_reset_mail(user_object=user)
#             return Response(status=status.HTTP_202_ACCEPTED,
#                             data={"detail": _("An email with password reset link has been sent.\n "
#                                               "The link will be valid for one day.")})
#
#     @action(detail=True, methods=['post'], url_path='reset-password/(?P<token>[^/w]+)',
#             permission_classes=(IsNotAuthenticated,))
#     def reset_password(self, request, pk, token):
#         if token:
#             user = get_object_or_404(self.queryset, pk=pk)
#             if password_reset_token.check_token(user=user, token=token):
#                 password_reset_serializer = PasswordResetSerializer(user=user, data=request.data)
#
#                 if password_reset_serializer.is_valid(raise_exception=True):
#                     UserDomainModel.set_new_password(user_object=user,
#                                                      new_password=password_reset_serializer.validated_data.get(
#                                                          "password"))
#                     return Response(status=status.HTTP_200_OK, data={"detail": _("The password has been changed.")})
#
#         return Response(status=status.HTTP_404_NOT_FOUND, data={"detail": _("The link is invalid.")})
#
#     @action(detail=False, methods=['post'], permission_classes=(IsAuthenticated,))
#     def request_email_address_change(self, request):
#         email_serializer = EmailChangeSerializer(user=request.user, data=request.data)
#
#         if email_serializer.is_valid(raise_exception=True):
#             UserDomainModel.send_email_address_change_mail(user_object=request.user,
#                                                            new_email_address=email_serializer.validated_data.get(
#                                                                "new_email"))
#             return Response(status=status.HTTP_202_ACCEPTED,
#                             data={"detail": _("An email with email address change link has been sent.\n "
#                                               "The link will be valid for one day.")})
#
#     # todo: all confirmation links must lead to the frontend's form view
#     # todo: this form will depend only on the pk and token from the url, not on the session's state
#
#     @action(detail=True, methods=['get'], url_path='change-email-address/(?P<token>[^/w]+)',
#             permission_classes=(permissions.AllowAny,))
#     # todo: endpoints modifying server's state shouldn't use safe methods in order to avoid csrf issues
#     def change_email_address(self, request, pk, token):
#         """ The frontend app is supposed to render the link from email (pointing to the frontend app) """
#         """ and in the appropriate view send the GET request to the same link but with backend's domain """
#
#         if token:
#             user = get_object_or_404(self.queryset, pk=pk)
#             if email_address_change_token.check_token(user=user, token=token):
#                 UserDomainModel.change_email_address(user_object=user)
#                 return Response(status=status.HTTP_200_OK,
#                                 data={"detail": _("The email address has been changed.")})
#         return Response(status=status.HTTP_404_NOT_FOUND, data={"detail": _("The link is invalid.")})
#
#
# class UserCreateViewSet(PermissionMixin, ListCreateAPIView):
#     queryset = UserDomainModel.get_active_standard_users()
#     permission_classes_by_action = {'create': (IsNotAuthenticated,),
#                                     'list': (permissions.IsAuthenticated,)}
#     filterset_fields = {
#         'username': ['iexact', 'contains', 'icontains', 'isnull']
#     }
#
#     def get_serializer_class(self):
#         if self.request.method in permissions.SAFE_METHODS:
#             return UserBasicSerializer
#         return UserCreateSerializer
