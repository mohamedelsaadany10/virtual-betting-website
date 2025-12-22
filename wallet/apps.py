from django.apps import AppConfig
from wallet.services import WalletService
from django.contrib.auth.models import User
from decimal import Decimal






from django.apps import AppConfig


class WalletConfig(AppConfig):
    """
    Wallet application configuration
    Handles app initialization and signal registration
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'wallet'
    verbose_name = 'Betting Wallet System'
    
    def ready(self):
        """
        Import signals when the app is ready
        This ensures signals are registered when Django starts
        """
        try:
            # Import signals to register them
            import wallet.signals
        except ImportError:
            pass

        
user = User.objects.get(username='testuser')
wallet = WalletService.create_wallet(user)


transaction = WalletService.deposit(
    wallet=wallet,
    amount=Decimal('100.00'),
    payment_method='CARD',
    description='Credit card deposit',
    ip_address='192.168.1.1'
) 
   
transaction = WalletService.place_bet(
    wallet=wallet,
    amount=Decimal('20.00'),
    bet_id=12345,
    description='Premier League match bet'
)
transaction = WalletService.credit_winnings(
    wallet=wallet,
    amount=Decimal('45.00'),
    bet_id=12345,
    description='Bet won'
)
withdrawal = WalletService.request_withdrawal(
    wallet=wallet,
    amount=Decimal('50.00'),
    payment_method='BANK',
    payment_details={
        'account_number': '1234567890',
        'bank_name': 'Test Bank'
    },
    ip_address='192.168.1.1'
)
