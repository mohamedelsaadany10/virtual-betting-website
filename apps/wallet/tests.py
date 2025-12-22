from django.test import TestCase, Client
from django.contrib.auth.models import User
from decimal import Decimal
from .models import Wallet, Transaction, WalletManager


class WalletModelTest(TestCase):
    """Test cases for Wallet model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.wallet = Wallet.objects.create(
            user=self.user,
            balance=Decimal('1000.00')
        )
    
    def test_wallet_creation(self):
        """Test wallet is created correctly"""
        self.assertEqual(self.wallet.user, self.user)
        self.assertEqual(self.wallet.balance, Decimal('1000.00'))
        self.assertEqual(self.wallet.currency, 'USD')
        self.assertTrue(self.wallet.is_active)
    
    def test_has_sufficient_balance(self):
        """Test balance checking"""
        self.assertTrue(self.wallet.has_sufficient_balance(500))
        self.assertTrue(self.wallet.has_sufficient_balance(1000))
        self.assertFalse(self.wallet.has_sufficient_balance(1500))
    
    def test_wallet_deduct(self):
        """Test deducting from wallet"""
        initial_balance = self.wallet.balance
        amount = Decimal('200.00')
        
        transaction = self.wallet.deduct(amount, "Test deduction")
        
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, initial_balance - amount)
        self.assertEqual(transaction.transaction_type, Transaction.DEBIT)
        self.assertEqual(transaction.amount, amount)
    
    def test_wallet_credit(self):
        """Test crediting to wallet"""
        initial_balance = self.wallet.balance
        amount = Decimal('500.00')
        
        transaction = self.wallet.credit(amount, "Test credit")
        
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, initial_balance + amount)
        self.assertEqual(transaction.transaction_type, Transaction.CREDIT)
        self.assertEqual(transaction.amount, amount)
    
    def test_insufficient_balance_raises_error(self):
        """Test that deducting more than balance raises error"""
        with self.assertRaises(ValueError):
            self.wallet.deduct(Decimal('2000.00'))


class TransactionModelTest(TestCase):
    """Test cases for Transaction model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.wallet = Wallet.objects.create(
            user=self.user,
            balance=Decimal('1000.00')
        )
    
    def test_transaction_creation(self):
        """Test transaction is created correctly"""
        transaction = Transaction.objects.create(
            wallet=self.wallet,
            transaction_type=Transaction.CREDIT,
            amount=Decimal('100.00'),
            balance_after=Decimal('1100.00'),
            description="Test transaction"
        )
        
        self.assertEqual(transaction.wallet, self.wallet)
        self.assertEqual(transaction.amount, Decimal('100.00'))
        self.assertEqual(transaction.status, Transaction.COMPLETED)
    
    def test_transaction_icon(self):
        """Test transaction icon display"""
        credit_trans = Transaction.objects.create(
            wallet=self.wallet,
            transaction_type=Transaction.CREDIT,
            amount=Decimal('100.00'),
            balance_after=Decimal('1100.00'),
            description="Credit"
        )
        
        debit_trans = Transaction.objects.create(
            wallet=self.wallet,
            transaction_type=Transaction.DEBIT,
            amount=Decimal('50.00'),
            balance_after=Decimal('950.00'),
            description="Debit"
        )
        
        self.assertEqual(credit_trans.get_transaction_icon(), '↑')
        self.assertEqual(debit_trans.get_transaction_icon(), '↓')


class WalletManagerTest(TestCase):
    """Test cases for WalletManager"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_create_wallet_for_user(self):
        """Test creating wallet for user"""
        wallet, created = WalletManager.create_wallet_for_user(self.user, 2000)
        
        self.assertTrue(created)
        self.assertEqual(wallet.user, self.user)
        self.assertEqual(wallet.balance, Decimal('2000.00'))
        
        # Test that calling again doesn't create duplicate
        wallet2, created2 = WalletManager.create_wallet_for_user(self.user)
        self.assertFalse(created2)
        self.assertEqual(wallet.id, wallet2.id)
    
    def test_process_bet_placement(self):
        """Test bet placement processing"""
        WalletManager.create_wallet_for_user(self.user, 1000)
        
        success, message, transaction = WalletManager.process_bet_placement(
            self.user, 
            Decimal('200.00')
        )
        
        self.assertTrue(success)
        self.assertIsNotNone(transaction)
        
        wallet = Wallet.objects.get(user=self.user)
        self.assertEqual(wallet.balance, Decimal('800.00'))
    
    def test_process_bet_placement_insufficient_funds(self):
        """Test bet placement with insufficient funds"""
        WalletManager.create_wallet_for_user(self.user, 100)
        
        success, message, transaction = WalletManager.process_bet_placement(
            self.user, 
            Decimal('200.00')
        )
        
        self.assertFalse(success)
        self.assertIsNone(transaction)
        self.assertIn("Insufficient balance", message)
    
    def test_process_bet_winning(self):
        """Test processing bet winnings"""
        WalletManager.create_wallet_for_user(self.user, 1000)
        
        success, message, transaction = WalletManager.process_bet_winning(
            self.user,
            Decimal('500.00'),
            bet_id=123
        )
        
        self.assertTrue(success)
        self.assertIsNotNone(transaction)
        
        wallet = Wallet.objects.get(user=self.user)
        self.assertEqual(wallet.balance, Decimal('1500.00'))
    
    def test_get_wallet_summary(self):
        """Test wallet summary generation"""
        WalletManager.create_wallet_for_user(self.user, 1000)
        
        summary = WalletManager.get_wallet_summary(self.user)
        
        self.assertIsNotNone(summary)
        self.assertEqual(summary['balance'], Decimal('1000.00'))
        self.assertEqual(summary['currency'], 'USD')
        self.assertTrue(summary['is_active'])


class WalletViewTest(TestCase):
    """Test cases for Wallet views"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.wallet = Wallet.objects.create(
            user=self.user,
            balance=Decimal('1000.00')
        )
    
    def test_wallet_dashboard_requires_login(self):
        """Test that wallet dashboard requires authentication"""
        response = self.client.get('/wallet/')
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_wallet_dashboard_authenticated(self):
        """Test wallet dashboard for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/wallet/')
        self.assertEqual(response.status_code, 200)
    
    def test_wallet_balance_api(self):
        """Test wallet balance API endpoint"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/wallet/api/balance/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['balance'], 1000.00)