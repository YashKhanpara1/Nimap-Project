import logging  # Added logging import
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Client, Project
from .serializers import ClientSerializer, ProjectSerializer
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound
from django.utils import timezone

# Configure logging
logger = logging.getLogger(__name__)  # Added logger configuration

class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access this view

    def create(self, request, *args, **kwargs):  # **Create method**
        logger.info("Creating a new client")  # Log before processing
        data = request.data.copy()  # Copy request data to modify
        data['created_by'] = request.user.id  # Automatically set the logged-in user as creator

        serializer = self.get_serializer(data=data)  # Use the serializer to validate data
        if serializer.is_valid():  # Check if the serializer data is valid
            client = serializer.save(created_by=request.user)  # Explicitly pass created_by to save method
            logger.info(f"Client created successfully: {client.id}")  # Log client creation success
            return Response(serializer.data, status=status.HTTP_201_CREATED)  # Return the created data
        logger.error(f"Client creation failed: {serializer.errors}")  # Log error if invalid
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  # Return errors if invalid

    def retrieve(self, request, *args, **kwargs):
        client = self.get_object()  # Get the client by ID
        logger.info(f"Retrieving client with ID: {client.id}")  # Log retrieval

        # Format response to include projects and related data in a customized way
        client_data = {
            'id': client.id,
            'client_name': client.client_name,
            'created_at': client.created_at.isoformat(),
            'updated_at': client.updated_at.isoformat(),
            'created_by': client.created_by.username  # Display username instead of user ID
        }

        # Get related projects and format project data
        projects = Project.objects.filter(client=client).values('id', 'project_name')
        projects_list = [{'id': project['id'], 'name': project['project_name']} for project in projects]
        client_data['projects'] = projects_list  # Include projects in the response

        return Response(client_data)

    def update(self, request, *args, **kwargs):
        logger.info("Updating a client")  # Log before processing
        partial = kwargs.pop('partial', False)  # Determine if the request is a partial update
        instance = self.get_object()  # Get the client instance to update
        instance.updated_at = timezone.now()  # Update the `updated_at` field
        serializer = self.get_serializer(instance, data=request.data, partial=partial)  # Ensure we serialize the instance
        
        if serializer.is_valid():  # Check if the serializer data is valid
            serializer.save()  # Save the updated client
            logger.info(f"Client updated successfully: {instance.id}")  # Log client update success
            return Response(serializer.data)  # Return the updated data
        logger.error(f"Client update failed: {serializer.errors}")  # Log error if invalid
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  # Return errors if invalid

    def destroy(self, request, *args, **kwargs):  # Method for handling DELETE requests
        logger.info("Deleting a client")  # Log before processing
        instance = self.get_object()  # Get the client instance to delete
        instance.delete()  # Delete the client instance
        logger.info(f"Client deleted successfully: {instance.id}")  # Log client deletion
        return Response(status=status.HTTP_204_NO_CONTENT)  # Return 204 No Content

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access this view

    def create(self, request, client_id, *args, **kwargs):  # Modified to accept client_id from URL
        logger.info(f"Attempting to create project for client_id: {client_id}")  # Log client ID
        try:
            client = Client.objects.get(id=client_id)  # Fetch the client using client_id
        except Client.DoesNotExist:
            logger.error(f"Client not found for ID: {client_id}")  # Log error if client not found
            raise NotFound("Client not found.")

        # Create the project with the logged-in user as the creator
        data = request.data.copy()
        data['created_by'] = request.user.id  # Automatically set the logged-in user as creator
        data['client'] = client.id  # Assign the client ID to the project data

        # **Updated logic to handle user IDs correctly**
        user_ids = request.data.get('users', [])
        if isinstance(user_ids, list) and all(isinstance(uid, int) for uid in user_ids):  # Ensure user IDs are a list of integers
            users = User.objects.filter(id__in=user_ids)  # Retrieve registered users by ID
        else:
            logger.error("Invalid user IDs format provided.")  # Log error for invalid format
            return Response({"users": ["Invalid format. Expected a list of user IDs."]}, status=status.HTTP_400_BAD_REQUEST)

        # Create the project with the provided data
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            project = serializer.save()  # Save the project
            project.users.set(users)  # Assign users to the project
            logger.info(f"Project created successfully: {project.id}")  # Log project creation success
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.error(f"Project creation failed: {serializer.errors}")  # Log error if invalid
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):  # Added method to list all projects assigned to logged-in user
        logger.info(f"Listing projects for user: {request.user.id}")  # Log project listing
        user_projects = Project.objects.filter(users=request.user)  # Filter projects by the logged-in user
        serializer = self.get_serializer(user_projects, many=True)
        return Response(serializer.data)  # Return the list of projects for the user
