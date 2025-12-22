# game/models.py
from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
import uuid


class DiceGame(models.Model):
    """Record of each dice game played"""
    BET_TYPES = [
        ('SINGLE', 'Single Number'),
        ('EVEN', 'Even Numbers'),
        ('ODD', 'Odd Numbers'),
        ('HIGH', 'High (4-6)'),
        ('LOW', 'Low (1-3)'),
    ]

    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('WON', 'Won'),
        ('LOST', 'Lost'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='games')
    bet_amount = models.DecimalField(max_digits=10, decimal_places=2)
    bet_type = models.CharField(max_length=20, choices=BET_TYPES)
    bet_value = models.IntegerField(null=True, blank=True)  # For SINGLE bets
    
    dice_result = models.IntegerField(null=True, blank=True)  # The rolled number (1-6)
    payout_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    status = models.CharField(max_choices=20, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'dice_games'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Game {self.id} - {self.user.username} - ${self.bet_amount}"
    
    @property
    def profit(self):
        """Calculate profit/loss"""
        if self.status == 'WON':
            return self.payout_amount - self.bet_amount
        elif self.status == 'LOST':
            return -self.bet_amount
        return Decimal('0.00')


class GameStats(models.Model):
    """User gaming statistics"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='game_stats')
    total_games = models.IntegerField(default=0)
    total_wins = models.IntegerField(default=0)
    total_losses = models.IntegerField(default=0)
    total_wagered = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_won = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    biggest_win = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    win_streak = models.IntegerField(default=0)
    current_streak = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'game_stats'
        verbose_name_plural = 'Game Stats'
    
    def __str__(self):
        return f"{self.user.username}'s Stats"
    
    @property
    def win_rate(self):
        """Calculate win percentage"""
        if self.total_games == 0:
            return 0
        return (self.total_wins / self.total_games) * 100
    
    @property
    def net_profit(self):
        """Calculate net profit/loss"""
        return self.total_won - self.total_wagered