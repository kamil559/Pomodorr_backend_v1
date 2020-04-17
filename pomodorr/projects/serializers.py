from django.utils.translation import gettext as _
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from pomodorr.projects.models import Project
from pomodorr.projects.services import PriorityDomainModel, ProjectDomainModel
from pomodorr.users.services import UserDomainModel


class ProjectSerializer(ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(write_only=True, default=serializers.CurrentUserDefault(),
                                              queryset=UserDomainModel.get_active_standard_users())
    priority = serializers.PrimaryKeyRelatedField(required=False, allow_null=True,
                                                  queryset=PriorityDomainModel.get_all_priorities())
    user_defined_ordering = serializers.IntegerField(min_value=1)

    def validate_priority(self, value):
        # todo: move the validation to project and task models
        user = self.context['request'].user
        if not PriorityDomainModel.get_priorities_for_user(user=user).filter(id=value.id).exists():
            raise serializers.ValidationError(
                _('Invalid pk "{pk_value}" - object does not exist.').format(pk_value=value.id), code='does_not_exist')

    def validate(self, data):
        #  Temporary solution for https://github.com/encode/django-rest-framework/issues/7100
        user = self.context['request'].user
        name = data.get('name') or None

        if name is not None and ProjectDomainModel.get_active_projects_for_user(user=user, name=name).exists():
            raise serializers.ValidationError(_('The fields name, user must make a unique set.'))
        return data

    class Meta:
        model = Project
        fields = ('id', 'name', 'priority', 'user_defined_ordering', 'user')
