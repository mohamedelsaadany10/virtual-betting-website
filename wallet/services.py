# game/services.py
from django.db import transaction
from decimal import Decimal
import random
from .models import DiceGame, GameStats
from wallet.services import WalletService
from wallet.models import Wallet
import logging

logger = logging.getLogger(__name__)


class DiceGameService:
    """Service for handling dice game logic"""
    
    # Payout multipliers
    PAYOUTS = {
        'SINGLE': Decimal('6.00'),   # Bet on single number: 6x
        'EVEN': Decimal('2.00'),      # Bet on even: 2x
        'ODD': Decimal('2.00'),       # Bet on odd: 2x
        'HIGH': Decimal('2.00'),      # Bet on 4-6: 2x
        'LOW': Decimal('2.00'),       # Bet on 1-3: 2x
    }
    
    @staticmethod
    def roll_dice():
        """Roll a dice and return result (1-6)"""
        return random.randint(1, 6)
    
    @staticmethod
    def check_win(bet_type, bet_value, dice_result):
        """Check if the bet won"""
        if bet_type == 'SINGLE':
            return dice_result == bet_value
        elif bet_type == 'EVEN':
            return dice_result % 2 == 0
        elif bet_type == 'ODD':
            return dice_result % 2 != 0
        elif bet_type == 'HIGH':
            return dice_result >= 4
        elif bet_type == 'LOW':
            return dice_result <= 3
        return False
    
    @staticmethod
    @transaction.atomic
    def place_bet(user, bet_amount, bet_type, bet_value=None):
        """Place a bet and play the game"""
        
        # Validate bet amount
        if bet_amount <= 0:
            raise ValueError("Bet amount must be positive")
        
        # Validate bet type
        if bet_type not in dict(DiceGame.BET_TYPES):
            raise ValueError("Invalid bet type")
        
        # Validate single number bet
        if bet_type == 'SINGLE':
            if not bet_value or bet_value < 1 or bet_value > 6:
                raise ValueError("For single number bet, choose a number between 1 and 6")
        
        # Get user's wallet
        wallet = Wallet.objects.select_for_update().get(user=user)
        
        # Check balance
        if wallet.balance < bet_amount:
            raise ValueError("Insufficient balance")
        
        # Deduct bet amount from wallet
        WalletService.place_bet(wallet, bet_amount, 0, f"{bet_type} bet")
        
        # Create game record
        game = DiceGame.objects.create(
            user=user,
            bet_amount=bet_amount,
            bet_type=bet_type,
            bet_value=bet_value,
            status='ACTIVE'
        )
        
        # Roll the dice
        dice_result = DiceGameService.roll_dice()
        game.dice_result = dice_result
        
        # Check if won
        is_win = DiceGameService.check_win(bet_type, bet_value, dice_result)
        
        if is_win:
            # Calculate payout
            multiplier = DiceGameService.PAYOUTS[bet_type]
            payout = bet_amount * multiplier
            game.payout_amount = payout
            game.status = 'WON'
            
            # Credit winnings
            WalletService.credit_winnings(wallet, payout, game.id, f"Won {bet_type} bet")
            
            logger.info(f"{user.username} WON ${payout} on {bet_type} bet")
        else:
            game.payout_amount = Decimal('0.00')
            game.status = 'LOST'
            logger.info(f"{user.username} LOST ${bet_amount} on {bet_type} bet")
        
        game.save()
        
        # Update stats
        DiceGameService.update_stats(user, game)
        
        return game
    
    @staticmethod
    def update_stats(user, game):
        """Update user's game statistics"""
        stats, created = GameStats.objects.get_or_create(user=user)
        
        stats.total_games += 1
        stats.total_wagered += game.bet_amount
        
        if game.status == 'WON':
            stats.total_wins += 1
            stats.total_won += game.payout_amount
            stats.current_streak += 1
            
            # Update biggest win
            profit = game.payout_amount - game.bet_amount
            if profit > stats.biggest_win:
                stats.biggest_win = profit
            
            # Update win streak
            if stats.current_streak > stats.win_streak:
                stats.win_streak = stats.current_streak
        else:
            stats.total_losses += 1
            stats.current_streak = 0
        
        stats.save()
    
    @staticmethod
    def get_game_history(user, limit=20):
        """Get user's recent games"""
        return DiceGame.objects.filter(user=user)[:limit]
    
    @staticmethod
    def get_leaderboard(limit=10):
        """Get top players by net profit"""
        return GameStats.objects.all().order_by('-total_won')[:limit]