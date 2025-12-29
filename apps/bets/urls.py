from django.urls import path
from . import views

app_name = 'bets'

urlpatterns = [
    # Main betting views
    path('place/<int:event_id>/', views.place_bet, name='place_bet'),
    path('history/', views.bet_history, name='history'),
    path('active/', views.active_bets, name='active_bets'),
    path('detail/<int:bet_id>/', views.bet_detail, name='detail'),
    
    # Bet actions
    path('cancel/<int:bet_id>/', views.cancel_bet, name='cancel_bet'),
    
    # API endpoints (for AJAX)
    path('api/calculate-payout/', views.calculate_payout_api, name='calculate_payout_api'),
    path('api/stats/', views.bet_stats_api, name='stats_api'),
    path('api/check-eligibility/<int:event_id>/', views.check_bet_eligibility, name='check_eligibility'),
]
