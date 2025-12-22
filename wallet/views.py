# game/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from decimal import Decimal
from .models import DiceGame, GameStats
from .services import DiceGameService
from wallet.models import Wallet


@login_required
def play_game(request):
    """Main game interface"""
    wallet = Wallet.objects.get(user=request.user)
    recent_games = DiceGame.objects.filter(user=request.user)[:5]
    stats, _ = GameStats.objects.get_or_create(user=request.user)
    
    context = {
        'wallet': wallet,
        'recent_games': recent_games,
        'stats': stats,
    }
    return render(request, 'game/play.html', context)


@login_required
def place_bet_api(request):
    """API endpoint to place a bet"""
    if request.method == 'POST':
        try:
            bet_amount = Decimal(request.POST.get('bet_amount'))
            bet_type = request.POST.get('bet_type')
            bet_value = request.POST.get('bet_value')
            
            if bet_value:
                bet_value = int(bet_value)
            
            # Place the bet
            game = DiceGameService.place_bet(
                user=request.user,
                bet_amount=bet_amount,
                bet_type=bet_type,
                bet_value=bet_value
            )
            
            # Get updated wallet balance
            wallet = Wallet.objects.get(user=request.user)
            
            return JsonResponse({
                'success': True,
                'game': {
                    'id': str(game.id),
                    'dice_result': game.dice_result,
                    'status': game.status,
                    'payout': float(game.payout_amount),
                    'profit': float(game.profit),
                },
                'balance': float(wallet.balance)
            })
            
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': 'An error occurred'
            }, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


@login_required
def game_history(request):
    """View game history"""
    games = DiceGame.objects.filter(user=request.user)
    stats = GameStats.objects.get(user=request.user)
    
    context = {
        'games': games,
        'stats': stats,
    }
    return render(request, 'game/history.html', context)


@login_required
def leaderboard(request):
    """View leaderboard"""
    top_players = DiceGameService.get_leaderboard(20)
    
    context = {
        'top_players': top_players,
    }
    return render(request, 'game/leaderboard.html', context)


@login_required
def user_stats(request):
    """View user statistics"""
    stats = GameStats.objects.get(user=request.user)
    recent_games = DiceGame.objects.filter(user=request.user)[:10]
    
    context = {
        'stats': stats,
        'recent_games': recent_games,
    }
    return render(request, 'game/stats.html', context)