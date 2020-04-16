# Generated by Django 2.2.11 on 2020-04-16 14:49

import colorfield.fields
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.manager
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Priority',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=128)),
                ('priority_level', models.PositiveIntegerField(default=1)),
                ('color', colorfield.fields.ColorField(default='#FF0000', max_length=18)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='priorities', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Priorities',
                'ordering': ('-priority_level',),
            },
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('is_removed', models.BooleanField(default=False)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=128)),
                ('user_defined_ordering', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='created at')),
                ('priority', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='projects', to='projects.Priority')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='projects', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Projects',
                'ordering': ('created_at', 'user_defined_ordering', '-priority__priority_level'),
            },
            managers=[
                ('all_objects', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('is_removed', models.BooleanField(default=False)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=128)),
                ('user_defined_ordering', models.PositiveIntegerField(default=0)),
                ('pomodoro_number', models.PositiveIntegerField()),
                ('due_date', models.DateField(default=django.utils.timezone.now)),
                ('reminder_date', models.DateTimeField(blank=True, null=True)),
                ('repeat_duration', models.DurationField(blank=True, default=None, null=True)),
                ('note', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='created at')),
                ('priority', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='projects.Priority')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='projects.Project')),
            ],
            options={
                'verbose_name_plural': 'Tasks',
                'ordering': ('created_at', 'user_defined_ordering', '-priority__priority_level'),
            },
            managers=[
                ('all_objects', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='TaskEvent',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('start', models.DateTimeField(verbose_name='start')),
                ('end', models.DateTimeField(verbose_name='end')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='created at')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='projects.Task')),
            ],
            options={
                'verbose_name_plural': 'TaskEvents',
                'ordering': ('created_at',),
            },
        ),
        migrations.CreateModel(
            name='SubTask',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=128)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='created at')),
                ('is_completed', models.BooleanField(default=False)),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sub_tasks', to='projects.Task')),
            ],
            options={
                'verbose_name_plural': 'SubTasks',
                'ordering': ('created_at',),
            },
        ),
        migrations.AddConstraint(
            model_name='task',
            constraint=models.UniqueConstraint(condition=models.Q(is_removed=False), fields=('name', 'project'), name='unique_project_task'),
        ),
        migrations.AddConstraint(
            model_name='subtask',
            constraint=models.UniqueConstraint(fields=('name', 'task'), name='unique_sub_task'),
        ),
        migrations.AddConstraint(
            model_name='project',
            constraint=models.UniqueConstraint(condition=models.Q(is_removed=False), fields=('name', 'user'), name='unique_user_project'),
        ),
        migrations.AddConstraint(
            model_name='priority',
            constraint=models.UniqueConstraint(fields=('priority_level', 'user'), name='unique_user_priority_level'),
        ),
    ]
