from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClientViewSet, ProjectViewSet

router = DefaultRouter()
router.register(r'clients', ClientViewSet)  # Register the Client viewset
router.register(r'projects', ProjectViewSet)  # Register the Project viewset

urlpatterns = [
    path('', include(router.urls)),  # Include all the routes from the router
    path('clients/<int:client_id>/projects/', ProjectViewSet.as_view({'post': 'create'})),  # Create a project for a specific client
    path('projects/', ProjectViewSet.as_view({'get': 'list'})),  # List projects assigned to the logged-in user
]
