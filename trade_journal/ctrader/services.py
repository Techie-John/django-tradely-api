import asyncio
from typing import List, Dict
from .models import CTraderAccount, CTrade
from ejtraderCT import Ctrader
from metatrade.utils import encrypt_password, decrypt_password, KEY


class CTraderService:
    def __init__(self):
        self._refresh_lock = asyncio.Lock()

    @staticmethod
    def login_account(user, server, sender_id, password):
        api = Ctrader(server, sender_id, password)
        status = api.isconnected()
        if status:
            CTraderAccount.objects.update_or_create(
                user=user,
                defaults={
                    'account': sender_id,
                    'server': server,
                    'password': encrypt_password(password),
                    'key_code': KEY,
                }
            )
        return status

    @staticmethod
    def fetch_accounts(user) -> List[Dict]:
        """Fetch all CTrader accounts for a user"""
        accounts = CTraderAccount.objects.filter(user=user)
        return [
            {
                'id': account.id,
                'account': account.account,
                'server': account.server,
                'demo_status': account.demo_status,
                # Add other relevant fields
            }
            for account in accounts
        ]

    @staticmethod
    def fetch_trades(user) -> List[Dict]:
        """Fetch all CTrader trades for a user"""
        trades = CTrade.objects.filter(trader_locker__user=user)
        return [
            {
                'id': trade.id,
                'ord_id': trade.ord_id,
                'name': trade.name,
                'side': trade.side,
                'amount': trade.amount,
                'price': trade.price,
                'actual_price': trade.actual_price,
                'pos_id': trade.pos_id,
                # Add other relevant fields
            }
            for trade in trades
        ]

    @staticmethod
    def get_trades(user) -> List[Dict]:
        account = CTraderAccount.objects.filter(user=user).first()
        password = decrypt_password(account.password, account.key_code)
        api = Ctrader(account.server, account.sender_id, password)
        status = api.isconnected()
        trades = []
        if status:
            trades = api.orders()
            for trade in trades:
                if trade['type'] == 'DEAL_TYPE_BALANCE':
                    continue
                CTrade.objects.update_or_create(
                    user=user,
                    ord_id=trade['ord_id'],
                    defaults={
                        'name': trade['name'],
                        'side': trade['side'],
                        'amount': trade['amount'],
                        'price': trade['price'],
                        'actual_price': trade['actual_price'],
                        'pos_id': trade['pos_id'],
                        'clid': trade['clid'],
                    })

        return trades