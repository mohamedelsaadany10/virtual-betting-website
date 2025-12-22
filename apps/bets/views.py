from apps.wallet.models import WalletManager
from decimal import Decimal

def place_bet_view(request):
    if request.method == 'POST':
        bet_amount = Decimal(request.POST.get('amount'))
        
        # Deduct from wallet
        success, message, transaction = WalletManager.process_bet_placement(
            user=request.user,
            bet_amount=bet_amount
        )
        
        if success:
            # Create bet record
            bet = Bet.objects.create(
                user=request.user,
                amount=bet_amount,
                # ... other fields
            )
            
            messages.success(request, 'Bet placed successfully!')
            return redirect('bets:active')
        else:
            messages.error(request, message)
            return redirect('wallet:dashboard')

def process_bet_result(bet_id, user_won=True):
    bet = Bet.objects.get(id=bet_id)
    
    if user_won:
        # Calculate winnings (e.g., 5x multiplier)
        winning_amount = bet.amount * Decimal('5')
        
        # Credit to wallet
        success, message, transaction = WalletManager.process_bet_winning(
            user=bet.user,
            winning_amount=winning_amount,
            bet_id=bet.id
        )
        
        if success:
            bet.status = 'won'
            bet.save()
            return True
    
    return False