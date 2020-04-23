from django.utils.translation import gettext as _
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from pomodorr.projects.models import Project, Priority
from pomodorr.projects.selectors import PrioritySelector, ProjectSelector
from pomodorr.users.services import UserDomainModel


class PrioritySerializer(serializers.ModelSerializer):
    priority_level = serializers.IntegerField(required=True, min_value=1)
    user = serializers.PrimaryKeyRelatedField(write_only=False, default=serializers.CurrentUserDefault(),
                                              queryset=UserDomainModel.get_active_standard_users())

    def validate(self, data):
        user = self.context['request'].user
        name = data.get('name') or None

        if name is not None and PrioritySelector.get_priorities_for_user(user=user, name=name).exists():
            raise serializers.ValidationError(_('Priority\'s name must be unique.'))
        return data

    class Meta:
        model = Priority
        fields = ('id', 'name', 'priority_level', 'color', 'user')


class ProjectSerializer(ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(write_only=True, default=serializers.CurrentUserDefault(),
                                              queryset=UserDomainModel.get_active_standard_users())
    priority = serializers.PrimaryKeyRelatedField(required=False, allow_null=True,
                                                  queryset=PrioritySelector.get_all_priorities())
    user_defined_ordering = serializers.IntegerField(min_value=1)

    def validate_priority(self, value):
        # todo: move the validation to project and task models
        user = self.context['request'].user
        if not PrioritySelector.get_priorities_for_user(user=user).filter(id=value.id).exists():
            raise serializers.ValidationError(
                _('Invalid pk "{pk_value}" - object does not exist.').format(pk_value=value.id), code='does_not_exist')

    def validate(self, data):
        #  Temporary solution for https://github.com/encode/django-rest-framework/issues/7100
        user = self.context['request'].user
        name = data.get('name') or None

        if name is not None and ProjectSelector.get_active_projects_for_user(user=user, name=name).exists():
            raise serializers.ValidationError(_('Project\'s name must be unique.'))
        return data

    class Meta:
        model = Project
        fields = ('id', 'name', 'priority', 'user_defined_ordering', 'user')
