from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.conf import settings
from rest_framework.test import APIClient
from decimal import Decimal
import datetime
from .email_service import BrevoEmailService
from django.utils import timezone
from unittest.mock import patch


from .models import CustomUser, TradeAccount, ManualTrade, TradeNote


User = get_user_model()


class UserTests(APITestCase):
    def test_user_registration(self):
        url = reverse('register')
        data = {'username': 'testuser', 'email': 'test@example.com', 'password': 'testpass123'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_login(self):
        url = reverse('register')
        self.client.post(url, {'username': 'testuser', 'email': 'test@example.com', 'password': 'testpass123'},
                         format='json')
        login_url = reverse('login')
        response = self.client.post(login_url, {'username': 'testuser', 'password': 'testpass123'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_token_obtain(self):
        url = reverse('register')
        self.client.post(url, {'username': 'testuser', 'email': 'test@example.com', 'password': 'testpass123'},
                         format='json')
        token_url = reverse('token_obtain_pair')
        response = self.client.post(token_url, {'username': 'testuser', 'password': 'testpass123'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_token_refresh(self):
        url = reverse('register')
        self.client.post(url, {'username': 'testuser', 'email': 'test@example.com', 'password': 'testpass123'},
                         format='json')
        token_url = reverse('token_obtain_pair')
        response = self.client.post(token_url, {'username': 'testuser', 'password': 'testpass123'}, format='json')
        refresh_token = response.data['refresh']

        refresh_url = reverse('token_refresh')
        refresh_response = self.client.post(refresh_url, {'refresh': refresh_token}, format='json')
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)
        
class TradeAccountTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)

    def test_create_trade_account(self):
        data = {
            'name': 'Test Account',
            'balance': 1000.00
        }
        # Update this line to use the correct URL path
        response = self.client.post('/api/users/trade-accounts/', data, format='json')
        print("Trade Account Creation Response:", response.content)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(TradeAccount.objects.count(), 1)
        self.assertEqual(TradeAccount.objects.first().name, 'Test Account')

class ManualTradeTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
        self.account = TradeAccount.objects.create(user=self.user, name='Test Account', balance=5000)

    def test_create_manual_trade(self):
        data = {
            'account': self.account.id,
            'trade_type': 'BUY',
            'symbol': 'AAPL',
            'quantity': 10,
            'price': 150.00,
            'trade_date': datetime.datetime.now().isoformat(),
            'notes': 'Test trade'
        }
        # Update this line to use the correct URL path
        response = self.client.post('/api/users/manual-trades/', data, format='json')
        print("Manual Trade Creation Response:", response.content)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(ManualTrade.objects.count(), 1)
        trade = ManualTrade.objects.first()
        self.assertEqual(trade.symbol, 'AAPL')
        self.assertEqual(trade.total_amount, Decimal('1500.00'))

class TradeStatisticsViewTests(TestCase):
    def setUp(self):
        # Create a test user
        self.user = CustomUser.objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='testpass123'
        )

        # Create a test trade account
        self.account = TradeAccount.objects.create(
            user=self.user,
            name='Test Account',
            balance=Decimal('10000.00')
        )

        # Create some test trades
        self.trades = [
            ManualTrade.objects.create(
                user=self.user,
                account=self.account,
                trade_type='BUY',
                symbol='AAPL',
                quantity=10,
                price=Decimal('150.00'),
                total_amount=Decimal('1500.00'),
                trade_date=timezone.now()
            ),
            ManualTrade.objects.create(
                user=self.user,
                account=self.account,
                trade_type='SELL',
                symbol='GOOGL',
                quantity=5,
                price=Decimal('1200.00'),
                total_amount=Decimal('6000.00'),
                trade_date=timezone.now()
            )
        ]

        # Set up API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_comprehensive_trade_statistics(self):
        """
        Test the comprehensive trade statistics endpoint
        """
        url = reverse('comprehensive-trade-statistics')
        response = self.client.get(url)

        # Check response status
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check overall statistics
        data = response.data
        self.assertIn('overall_statistics', data)
        self.assertEqual(data['overall_statistics']['total_trades'], 2)
        self.assertEqual(
            data['overall_statistics']['total_invested'], 
            Decimal('7500.00')
        )

        # Check symbol performances
        self.assertIn('symbol_performances', data)
        self.assertEqual(len(data['symbol_performances']), 2)

        # Check monthly trade summary
        self.assertIn('monthly_trade_summary', data)
        self.assertTrue(len(data['monthly_trade_summary']) > 0)

    def test_trade_account_performance(self):
        """
        Test the trade account performance endpoint
        """
        url = reverse('trade-account-performance')
        response = self.client.get(url)

        # Check response status
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check account performances
        data = response.data
        self.assertIn('account_performances', data)
        self.assertEqual(len(data['account_performances']), 1)

        account_perf = data['account_performances'][0]
        self.assertEqual(account_perf['account_id'], self.account.id)
        self.assertEqual(account_perf['total_trades'], 2)
        self.assertEqual(
            account_perf['total_traded_amount'], 
            Decimal('7500.00')
        )
class TradeNoteTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
        self.account = TradeAccount.objects.create(user=self.user, name='Test Account', balance=5000)
        self.trade = ManualTrade.objects.create(
            user=self.user, 
            account=self.account, 
            trade_type='BUY', 
            symbol='AAPL', 
            quantity=10, 
            price=150.00, 
            trade_date=timezone.now()
        )

    def test_create_trade_note(self):
        data = {
            'trade': self.trade.id,
            'trade_note': 'Test trade note'
        }
        response = self.client.post('/api/users/trade-notes/', data, format='json')
        print("Response Status:", response.status_code)
        print("Response Content:", response.content)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TradeNote.objects.count(), 1)
        note = TradeNote.objects.first()
        self.assertEqual(note.trade_note, 'Test trade note')

    def test_create_trade_note_with_note_date(self):
        data = {
            'note_date': '2022-01-01',
            'trade_note': 'Test trade note'
        }
        response = self.client.post('/api/users/trade-notes/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TradeNote.objects.count(), 1)
        note = TradeNote.objects.first()
        self.assertEqual(note.trade_note, 'Test trade note')
        self.assertEqual(note.note_date, datetime.date(2022, 1, 1))

    def test_get_trade_notes(self):
        TradeNote.objects.create(user=self.user, trade=self.trade, trade_note='Test trade note 1')
        TradeNote.objects.create(user=self.user, trade=self.trade, trade_note='Test trade note 2')
        response = self.client.get('/api/users/trade-notes/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_get_trade_note(self):
        note = TradeNote.objects.create(user=self.user, trade=self.trade, trade_note='Test trade note')
        response = self.client.get(f'/api/users/trade-notes/{note.id}/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['trade_note'], 'Test trade note')

    def test_update_trade_note(self):
        note = TradeNote.objects.create(user=self.user, trade=self.trade, trade_note='Test trade note')
        data = {
            'trade_note': 'Updated test trade note',
            'trade': self.trade.id  # Include the trade field
        }
        response = self.client.put(f'/api/users/trade-notes/{note.id}/', data, format='json')
        print("Update Response Status:", response.status_code)
        print("Update Response Content:", response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        note.refresh_from_db()
        self.assertEqual(note.trade_note, 'Updated test trade note')
        
    def test_delete_trade_note(self):
        note = TradeNote.objects.create(user=self.user, trade=self.trade, trade_note='Test trade note')
        response = self.client.delete(f'/api/users/trade-notes/{note.id}/', format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(TradeNote.objects.count(), 0)

class BrevoEmailServiceTest(TestCase):
    def setUp(self):
        self.email_service = BrevoEmailService()
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com'
        )

    @patch('requests.post')
    def test_send_registration_email(self, mock_post):
        # Mock successful email send
        mock_post.return_value.json.return_value = {'messageId': '123'}
        mock_post.return_value.raise_for_status.return_value = None

        success, response = self.email_service.send_registration_email(
            user_email=self.user.email, 
            username=self.user.username
        )

        self.assertTrue(success)
        mock_post.assert_called_once()

    @patch('requests.post')
    def test_send_payment_confirmation_email(self, mock_post):
        # Mock successful email send
        mock_post.return_value.json.return_value = {'messageId': '456'}
        mock_post.return_value.raise_for_status.return_value = None

        success, response = self.email_service.send_payment_confirmation_email(
            user_email=self.user.email, 
            username=self.user.username,
            amount=100.00
        )

        self.assertTrue(success)
        mock_post.assert_called_once()
