from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
from apps.events.models import Event


class Bet(models.Model):
    """
    Represents a bet placed by a user on an event
    """
    
    # Bet Type Choices
    TEAM_A_WIN = 'team_a_win'
    TEAM_B_WIN = 'team_b_win'
    DRAW = 'draw'
    OVER = 'over'
    UNDER = 'under'
    
    BET_TYPE_CHOICES = [
        (TEAM_A_WIN, 'Team A Wins'),
        (TEAM_B_WIN, 'Team B Wins'),
        (DRAW, 'Draw'),
        (OVER, 'Over'),
        (UNDER, 'Under'),
    ]
    
    # Bet Status Choices
    PENDING = 'pending'
    WON = 'won'
    LOST = 'lost'
    CANCELLED = 'cancelled'
    VOID = 'void'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (WON, 'Won'),
        (LOST, 'Lost'),
        (CANCELLED, 'Cancelled'),
        (VOID, 'Void'),
    ]
    
    # Core Fields
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='bets'
    )
    event = models.ForeignKey(
        Event, 
        on_delete=models.CASCADE, 
        related_name='bets'
    )
    
    # Bet Details
    bet_type = models.CharField(
        max_length=20, 
        choices=BET_TYPE_CHOICES,
        help_text="Type of bet placed"
    )
    stake = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('1.00'))],
        help_text="Amount wagered"
    )
    odds = models.DecimalField(
        max_digits=6, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('1.01'))],
        help_text="Odds at time of bet placement"
    )
    potential_payout = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        help_text="Potential winnings if bet wins"
    )
    
    # Status and Result
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default=PENDING
    )
    actual_payout = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Actual amount paid out"
    )
    
    # Timestamps
    placed_at = models.DateTimeField(auto_now_add=True)
    settled_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional Info
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    notes = models.TextField(blank=True, help_text="Admin notes or bet details")
    
    class Meta:
        db_table = 'bets'
        ordering = ['-placed_at']
        indexes = [
            models.Index(fields=['user', '-placed_at']),
            models.Index(fields=['event', 'status']),
            models.Index(fields=['status']),
        ]
        verbose_name = 'Bet'
        verbose_name_plural = 'Bets'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_bet_type_display()} on {self.event} - ${self.stake}"
    
    def save(self, *args, **kwargs):
        """Override save to auto-calculate potential payout if not set"""
        if not self.potential_payout:
            self.potential_payout = self.stake * self.odds
        super().save(*args, **kwargs)
    
    # Status Check Methods
    def is_pending(self):
        """Check if bet is still pending"""
        return self.status == self.PENDING
    
    def is_settled(self):
        """Check if bet has been settled"""
        return self.status in [self.WON, self.LOST, self.CANCELLED, self.VOID]
    
    def can_be_cancelled(self):
        """
        Check if bet can be cancelled
        Rules: Only pending bets before event starts can be cancelled
        """
        if not self.is_pending():
            return False
        
        # Check if event has started
        if hasattr(self.event, 'start_time'):
            return timezone.now() < self.event.start_time
        
        return True
    
    # Action Methods
    def mark_as_won(self, payout_amount=None):
        """Mark bet as won and record payout"""
        if not self.is_pending():
            raise ValueError("Only pending bets can be marked as won")
        
        self.status = self.WON
        self.actual_payout = payout_amount or self.potential_payout
        self.settled_at = timezone.now()
        self.save()
    
    def mark_as_lost(self):
        """Mark bet as lost"""
        if not self.is_pending():
            raise ValueError("Only pending bets can be marked as lost")
        
        self.status = self.LOST
        self.actual_payout = Decimal('0.00')
        self.settled_at = timezone.now()
        self.save()
    
    def mark_as_cancelled(self):
        """Mark bet as cancelled"""
        if not self.can_be_cancelled():
            raise ValueError("This bet cannot be cancelled")
        
        self.status = self.CANCELLED
        self.settled_at = timezone.now()
        self.save()
    
    def mark_as_void(self, reason=""):
        """Mark bet as void (refund stake)"""
        self.status = self.VOID
        self.actual_payout = self.stake  # Refund stake
        self.settled_at = timezone.now()
        if reason:
            self.notes = f"Voided: {reason}"
        self.save()
    
    # Calculation Methods
    def calculate_profit(self):
        """Calculate profit (payout - stake)"""
        if self.status == self.WON:
            return self.actual_payout - self.stake
        return Decimal('0.00')
    
    def get_roi(self):
        """Calculate Return on Investment percentage"""
        if self.status == self.WON and self.stake > 0:
            return ((self.actual_payout - self.stake) / self.stake) * 100
        return Decimal('0.00')
    
    # Display Methods
    def get_status_badge_class(self):
        """Return CSS class for status badge"""
        status_classes = {
            self.PENDING: 'warning',
            self.WON: 'success',
            self.LOST: 'danger',
            self.CANCELLED: 'secondary',
            self.VOID: 'info',
        }
        return status_classes.get(self.status, 'secondary')
    
    def get_status_icon(self):
        """Return icon for status"""
        status_icons = {
            self.PENDING: '⏳',
            self.WON: '✅',
            self.LOST: '❌',
            self.CANCELLED: '🚫',
            self.VOID: '↩️',
        }
        return status_icons.get(self.status, '❓')
    
    # Class Methods for Statistics
    @classmethod
    def get_user_stats(cls, user):
        """
        Get comprehensive betting statistics for a user
        Returns dict with various stats
        """
        from django.db.models import Sum, Count, Avg, Q
        
        bets = cls.objects.filter(user=user)
        
        total_bets = bets.count()
        pending_bets = bets.filter(status=cls.PENDING).count()
        won_bets = bets.filter(status=cls.WON).count()
        lost_bets = bets.filter(status=cls.LOST).count()
        
        # Financial stats
        total_staked = bets.aggregate(total=Sum('stake'))['total'] or Decimal('0.00')
        total_won = bets.filter(status=cls.WON).aggregate(total=Sum('actual_payout'))['total'] or Decimal('0.00')
        total_pending_stake = bets.filter(status=cls.PENDING).aggregate(total=Sum('stake'))['total'] or Decimal('0.00')
        
        # Calculate net profit/loss
        net_profit = total_won - (total_staked - total_pending_stake)
        
        # Win rate
        settled_bets = won_bets + lost_bets
        win_rate = (won_bets / settled_bets * 100) if settled_bets > 0 else Decimal('0.00')
        
        # Average odds
        avg_odds = bets.aggregate(avg=Avg('odds'))['avg'] or Decimal('0.00')
        
        return {
            'total_bets': total_bets,
            'pending_bets': pending_bets,
            'won_bets': won_bets,
            'lost_bets': lost_bets,
            'total_staked': total_staked,
            'total_won': total_won,
            'total_pending_stake': total_pending_stake,
            'net_profit': net_profit,
            'win_rate': round(win_rate, 2),
            'avg_odds': round(avg_odds, 2),
        }
    
    @classmethod
    def get_pending_bets_for_event(cls, event):
        """Get all pending bets for a specific event"""
        return cls.objects.filter(event=event, status=cls.PENDING)
    
    @classmethod
    def get_recent_wins(cls, user, limit=5):
        """Get user's recent winning bets"""
        return cls.objects.filter(
            user=user, 
            status=cls.WON
        ).order_by('-settled_at')[:limit]
