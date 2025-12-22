from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from decimal import Decimal
from .models import Wallet, Transaction, WalletManager


@login_required
def wallet_dashboard(request):
    """
    Main wallet dashboard view - connects to your interactive interface
    """
    # Get or create wallet for the user
    wallet, created = WalletManager.create_wallet_for_user(request.user)
    
    # Get wallet summary
    summary = WalletManager.get_wallet_summary(request.user)
    
    # Get recent transactions (last 10)
    recent_transactions = WalletManager.get_transaction_history(request.user, limit=10)
    
    # Calculate statistics for the dashboard
    total_bets = Transaction.objects.filter(
        wallet=wallet,
        transaction_type=Transaction.DEBIT,
        description__icontains='bet'
    ).count()
    
    active_bets_count = 3  # You'll replace this with actual logic from bets app
    
    # Calculate win rate
    total_wins = Transaction.objects.filter(
        wallet=wallet,
        transaction_type=Transaction.CREDIT,
        description__icontains='winning'
    ).count()
    
    win_rate = (total_wins / total_bets * 100) if total_bets > 0 else 0
    
    # Calculate total winnings
    total_winnings = Transaction.objects.filter(
        wallet=wallet,
        transaction_type=Transaction.CREDIT,
        description__icontains='winning',
        status=Transaction.COMPLETED
    ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
    
    context = {
        'wallet': wallet,
        'summary': summary,
        'transactions': recent_transactions,
        'total_bets': total_bets,
        'active_bets_count': active_bets_count,
        'win_rate': round(win_rate, 1),
        'total_winnings': total_winnings,
    }
    
    return render(request, 'wallet/dashboard.html', context)


@login_required
def transaction_history(request):
    """
    View all transactions with filtering
    """
    wallet = get_object_or_404(Wallet, user=request.user)
    
    # Get filter parameters
    transaction_type = request.GET.get('type', '')
    status = request.GET.get('status', '')
    
    # Get all transactions
    transactions = wallet.transactions.all()
    
    # Apply filters
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    if status:
        transactions = transactions.filter(status=status)
    
    context = {
        'wallet': wallet,
        'transactions': transactions,
        'transaction_type': transaction_type,
        'status': status,
    }
    
    return render(request, 'wallet/transaction_history.html', context)


@login_required
@require_http_methods(["POST"])
def add_funds(request):
    """
    Add funds to wallet - connects to the Add Funds modal
    """
    try:
        amount = Decimal(request.POST.get('amount', '0'))
        
        # Validation
        if amount <= 0:
            return JsonResponse({
                'success': False,
                'error': 'Amount must be greater than zero'
            }, status=400)
        
        if amount > 10000:
            return JsonResponse({
                'success': False,
                'error': 'Maximum deposit amount is $10,000'
            }, status=400)
        
        # Get wallet
        wallet = get_object_or_404(Wallet, user=request.user)
        
        # Add funds using atomic transaction
        with transaction.atomic():
            trans = wallet.credit(amount, f"Deposit - Added ${amount}")
        
        # Return success response with updated data
        return JsonResponse({
            'success': True,
            'message': f'Successfully added ${amount} to your wallet',
            'new_balance': float(wallet.balance),
            'transaction': {
                'id': trans.id,
                'amount': float(trans.amount),
                'description': trans.description,
                'created_at': trans.created_at.strftime('%b %d, %Y - %H:%M'),
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def withdraw_funds(request):
    """
    Withdraw funds from wallet - connects to the Withdraw modal
    """
    try:
        amount = Decimal(request.POST.get('amount', '0'))
        
        # Get wallet
        wallet = get_object_or_404(Wallet, user=request.user)
        
        # Validation
        if amount <= 0:
            return JsonResponse({
                'success': False,
                'error': 'Amount must be greater than zero'
            }, status=400)
        
        if not wallet.has_sufficient_balance(amount):
            return JsonResponse({
                'success': False,
                'error': f'Insufficient balance. Available: ${wallet.balance}'
            }, status=400)
        
        # Withdraw funds using atomic transaction
        with transaction.atomic():
            trans = wallet.deduct(amount, f"Withdrawal - ${amount}")
        
        # Return success response
        return JsonResponse({
            'success': True,
            'message': f'Successfully withdrew ${amount} from your wallet',
            'new_balance': float(wallet.balance),
            'transaction': {
                'id': trans.id,
                'amount': float(trans.amount),
                'description': trans.description,
                'created_at': trans.created_at.strftime('%b %d, %Y - %H:%M'),
            }
        })
        
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def wallet_balance_api(request):
    """
    API endpoint to get current wallet balance
    Used for real-time balance updates in the interface
    """
    try:
        wallet = Wallet.objects.get(user=request.user)
        summary = WalletManager.get_wallet_summary(request.user)
        
        return JsonResponse({
            'success': True,
            'balance': float(wallet.balance),
            'currency': wallet.currency,
            'is_active': wallet.is_active,
            'total_deposited': float(summary['total_deposited']),
            'total_withdrawn': float(summary['total_withdrawn']),
            'transaction_count': summary['transaction_count'],
        })
    except Wallet.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Wallet not found'
        }, status=404)


@login_required
def check_balance(request):
    """
    Check if user has sufficient balance for a bet
    Used before placing bets
    """
    try:
        amount = Decimal(request.GET.get('amount', '0'))
        wallet = Wallet.objects.get(user=request.user)
        
        has_balance = wallet.has_sufficient_balance(amount)
        
        return JsonResponse({
            'success': True,
            'has_sufficient_balance': has_balance,
            'current_balance': float(wallet.balance),
            'required_amount': float(amount),
            'message': 'Sufficient balance' if has_balance else 'Insufficient balance'
        })
    except Wallet.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Wallet not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
def get_wallet_stats(request):
    """
    Get comprehensive wallet statistics for the dashboard
    """
    try:
        wallet = Wallet.objects.get(user=request.user)
        summary = WalletManager.get_wallet_summary(request.user)
        
        # Calculate total winnings
        total_winnings = Transaction.objects.filter(
            wallet=wallet,
            transaction_type=Transaction.CREDIT,
            description__icontains='winning',
            status=Transaction.COMPLETED
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        
        # Calculate total bets
        total_bets = Transaction.objects.filter(
            wallet=wallet,
            transaction_type=Transaction.DEBIT,
            description__icontains='bet'
        ).count()
        
        # Calculate wins
        total_wins = Transaction.objects.filter(
            wallet=wallet,
            transaction_type=Transaction.CREDIT,
            description__icontains='winning'
        ).count()
        
        win_rate = (total_wins / total_bets * 100) if total_bets > 0 else 0
        
        return JsonResponse({
            'success': True,
            'stats': {
                'balance': float(wallet.balance),
                'total_deposited': float(summary['total_deposited']),
                'total_withdrawn': float(summary['total_withdrawn']),
                'total_winnings': float(total_winnings),
                'total_bets': total_bets,
                'total_wins': total_wins,
                'win_rate': round(win_rate, 1),
                'member_since': summary['created_at'].strftime('%b %d, %Y'),
            }
        })
    except Wallet.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Wallet not found'
        }, status=404)


@login_required
def get_recent_transactions(request):
    """
    Get recent transactions for live updates
    """
    try:
        limit = int(request.GET.get('limit', 10))
        transactions = WalletManager.get_transaction_history(request.user, limit=limit)
        
        transactions_data = []
        for trans in transactions:
            transactions_data.append({
                'id': trans.id,
                'type': trans.transaction_type,
                'amount': float(trans.amount),
                'description': trans.description,
                'status': trans.status,
                'balance_after': float(trans.balance_after),
                'created_at': trans.created_at.strftime('%b %d, %Y - %H:%M'),
                'icon': trans.get_transaction_icon(),
                'css_class': trans.get_transaction_class(),
            })
        
        return JsonResponse({
            'success': True,
            'transactions': transactions_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# Integration functions for Bets app
@login_required
def process_bet_payment(request, bet_amount):
    """
    Function to be called from bets app when placing a bet
    """
    success, message, transaction = WalletManager.process_bet_placement(
        user=request.user,
        bet_amount=Decimal(str(bet_amount))
    )
    
    return success, message, transaction


@login_required
def process_bet_win(request, winning_amount, bet_id=None):
    """
    Function to be called from bets app when user wins
    """
    success, message, transaction = WalletManager.process_bet_winning(
        user=request.user,
        winning_amount=Decimal(str(winning_amount)),
        bet_id=bet_id
    )
    
    return success, message, transaction