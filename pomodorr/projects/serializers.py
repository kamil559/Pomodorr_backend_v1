from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from pomodorr.projects.models import Project
from pomodorr.users.services import UserDomainModel


class ProjectSerializer(ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(write_only=True, default=serializers.CurrentUserDefault(),
                                              queryset=UserDomainModel.get_active_standard_users())

    class Meta:
        model = Project
        fields = ('id', 'name', 'priority', 'color', 'user_defined_ordering', 'user')
