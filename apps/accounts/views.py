import random
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from apps.wallet.models import Wallet

@login_required
def home_view(request):
    # Get the user's wallet
    user_wallet, created = Wallet.objects.get_or_create(user=request.user)
    result_msg = None
    
    if request.method == 'POST':
        try:
            amount = float(request.POST.get('amount', 0))
            side = request.POST.get('side')
            
            if 0 < amount <= user_wallet.balance:
                outcome = random.choice(['Heads', 'Tails'])
                if side == outcome:
                    user_wallet.balance += amount
                    result_msg = f"WIN! The coin landed on {outcome}. You won IDR {amount}!"
                else:
                    user_wallet.balance -= amount
                    result_msg = f"LOSS! The coin landed on {outcome}. You lost IDR {amount}."
                user_wallet.save()
            else:
                result_msg = "Invalid amount or insufficient funds."
        except (ValueError, TypeError):
            result_msg = "Please enter a valid number."
            
    return render(request, 'home.html', {'result_msg': result_msg, 'balance': user_wallet.balance})