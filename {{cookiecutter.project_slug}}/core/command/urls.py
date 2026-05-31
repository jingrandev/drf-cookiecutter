from django.urls import include
from django.urls import path

from core.restframework.routers import get_router

from .endpoints import CommandViewSet

router = get_router()
router.register("commands", CommandViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
