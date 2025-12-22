from django.urls import path
from . import views

app_name = 'wallet'

urlpatterns = [
    # Main Dashboard
    path('', views.wallet_dashboard, name='dashboard'),
    
    # Transaction Management
    path('transactions/', views.transaction_history, name='transactions'),
    path('transactions/recent/', views.get_recent_transactions, name='recent_transactions'),
    
    # Wallet Operations (POST requests)
    path('add-funds/', views.add_funds, name='add_funds'),
    path('withdraw/', views.withdraw_funds, name='withdraw_funds'),
    
    # API Endpoints (GET requests for AJAX)
    path('api/balance/', views.wallet_balance_api, name='balance_api'),
    path('api/check-balance/', views.check_balance, name='check_balance'),
    path('api/stats/', views.get_wallet_stats, name='stats_api'),
]