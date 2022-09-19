from django.urls import path

from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create", views.create_listing, name="create"),
    path("watch", views.watch, name="watch"),
    path("category", views.category, name="category"),
    path("category/<str:category_list>", views.category_list, name="category_list"),
    path("<str:listing>", views.listing, name="listing")
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)