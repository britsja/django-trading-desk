from django.test import TestCase
from decimal import Decimal
from .models import PropAccount, TradeRecord

class TradingDeskLogicTests(TestCase):

  def setUp(self):
    self.account = PropAccount.objects.create(
      account_id="TEST-FUNDED-01",
      initial_balance=Decimal("50000.00"),
      current_balance=Decimal("50000.00"),
      max_daily_drawdown_limit=Decimal("47500.00")
    )

  def test_balance_recalculation_with_closed_trades(self):
      TradeRecord.objects.create(
          account=self.account, ticker="NAS100", action="BUY",
          execution_price=Decimal("19500.00"), pnl=Decimal("1500.00"), is_closed=True
      )
      TradeRecord.objects.create(
          account=self.account, ticker="EURUSD", action="SELL",
          execution_price=Decimal("1.1100"), pnl=Decimal("-200.00"), is_closed=True
      )

      calculated_balance = self.account.recalculate_balance_from_trades()
    
      self.assertEqual(calculated_balance, Decimal("51300.00"))
      self.assertEqual(self.account.current_balance, Decimal("51300.00"))

  def test_drawdown_breach_detection(self):
     TradeRecord.objects.create(
        account=self.account, ticker="USDZAR", action="SELL",
        execution_price=Decimal("16.6"), pnl=Decimal("-10000.00"), is_closed=True
     )

     self.account.recalculate_balance_from_trades()

     breach_occured = self.account.check_drawdown_breach()

     self.assertTrue(breach_occured)
     self.assertFalse(self.account.is_active)

  def test_win_rate_calculcation(self):
     TradeRecord.objects.create(
        account=self.account, ticker="USDZAR", action="SELL",
        execution_price=Decimal("16.6"), pnl=Decimal("500.00"), is_closed=True
      )
     TradeRecord.objects.create(
        account=self.account, ticker="GBPJPY", action="SELL",
        execution_price=Decimal("200.10"), pnl=Decimal("-300.00"), is_closed=True
      )
     TradeRecord.objects.create(
        account=self.account, ticker="EURGBP", action="BUY",
        execution_price=Decimal("1.32"), pnl=Decimal("200.00"), is_closed=True
      )

     self.account.recalculate_balance_from_trades()

     win_rate = self.account.win_rate

     self.assertEqual(win_rate, Decimal("66.67"))