from rest_framework import serializers
from .models import Client, Project
from django.contrib.auth.models import User

# Serializer for Projects
class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'project_name', 'client', 'users', 'created_at', 'created_by']  # Adjust fields as necessary

# Serializer for Clients
class ClientSerializer(serializers.ModelSerializer):
    projects = ProjectSerializer(many=True, read_only=True)  # Include related projects
    created_by = serializers.CharField(source='created_by.username', read_only=True)  # Automatically fetch the username
    updated_at = serializers.DateTimeField(read_only=True)  # **Field for updated_at**

    class Meta:
        model = Client
        fields = ['id', 'client_name', 'created_at', 'updated_at', 'created_by', 'projects']  # **Updated to include updated_at**
