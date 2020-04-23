from django.utils.translation import gettext as _
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from pomodorr.projects.models import Project, Priority, Task
from pomodorr.projects.selectors import PrioritySelector, ProjectSelector, TaskSelector
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
        user = self.context['request'].user
        if not PrioritySelector.get_priorities_for_user(user=user).filter(id=value.id).exists():
            raise serializers.ValidationError(
                _('The chosen priority does not exist.').format(pk_value=value.id), code='does_not_exist')
        return value

    def validate(self, data):
        #  Temporary solution for https://github.com/encode/django-rest-framework/issues/7100
        user = self.context['request'].user
        name = data.get('name') or None

        if name is not None and ProjectSelector.get_active_projects_for_user(user=user, name=name).exists():
            raise serializers.ValidationError({'name': _('Project\'s name must be unique.')})
        return data

    class Meta:
        model = Project
        fields = ('id', 'name', 'priority', 'user_defined_ordering', 'user')


class TaskSerializer(serializers.ModelSerializer):
    project = serializers.PrimaryKeyRelatedField(
        required=True,
        queryset=ProjectSelector.get_all_active_projects()
    )
    priority = serializers.PrimaryKeyRelatedField(
        required=False, allow_null=True,
        queryset=PrioritySelector.get_all_priorities()
    )
    user_defined_ordering = serializers.IntegerField(min_value=1)

    def validate_project(self, value):
        user = self.context['request'].user
        if not ProjectSelector.get_active_projects_for_user(user=user, id=value.id).exists():
            raise serializers.ValidationError(
                _('The chosen project does not exist.'))
        return value

    def validate_priority(self, value):
        user = self.context['request'].user

        if value and not PrioritySelector.get_priorities_for_user(user=user).filter(id=value.id).exists():
            raise serializers.ValidationError(
                _('The chosen priority does not exist.').format(pk_value=value.id), code='does_not_exist')
        return value

    def validate(self, data):
        # Temporary solution for https://github.com/encode/django-rest-framework/issues/7100
        user = self.context['request'].user
        name = data.get('name') or None
        project = data.get('project') or None

        if name is not None and project is not None and TaskSelector.get_all_non_removed_tasks_for_user(
            user=user, name=name, project=project).exists():
            raise serializers.ValidationError({'name': _('Task\'s name must be unique.')})
        return data

    class Meta:
        model = Task
        fields = (
            'id', 'name', 'status', 'project', 'priority', 'user_defined_ordering', 'pomodoro_number',
            'pomodoro_length', 'due_date', 'reminder_date', 'repeat_duration', 'note')

    def to_representation(self, instance):
        data = super(TaskSerializer, self).to_representation(instance=instance)
        data['status'] = instance.get_status_display()
        return data
