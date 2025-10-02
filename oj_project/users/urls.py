from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('api/profile/update/', views.update_profile_api, name='update_profile_api'),
    path('api/profile/avatar/', views.upload_avatar_api, name='upload_avatar_api'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
]

