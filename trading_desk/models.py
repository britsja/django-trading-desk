from django.db import models
from django.db.models import Sum
from decimal import Decimal

class PropAccount(models.Model):
  account_id = models.CharField(max_length=50, unique=True)
  initial_balance = models.DecimalField(max_digits=12, decimal_places=2)
  current_balance = models.DecimalField(max_digits=12, decimal_places=2)
  max_daily_drawdown_limit = models.DecimalField(max_digits=12, decimal_places=2)
  is_active = models.BooleanField(default=True)
  created_at = models.DateTimeField(auto_now_add=True)

  def __str__(self):
    return f"Account: {self.account_id} | Balance: {self.current_balance} | Active: {self.is_active}"

  def recalculate_balance_from_trades(self) -> Decimal:
    trades_totals = self.trades.filter(is_closed=True).aggregate(total_pnl=Sum('pnl'))
    actual_pnl = trades_totals.get('total_pnl') or 0
    self.current_balance = Decimal(self.initial_balance) + Decimal(actual_pnl)
    self.save()
    return self.current_balance

  def check_drawdown_breach(self) -> bool:
    if self.current_balance <= self.max_daily_drawdown_limit:
      self.is_active = False
      self.save()
      return True
    return False

  @property
  def win_rate(self) -> Decimal:
    total_trades = self.trades.filter(is_closed=True).count()
    profitable_trades = self.trades.filter(is_closed=True, pnl__gt=0).count()
    
    if total_trades == 0:
        return Decimal('0.00')
    
    win_ratio = profitable_trades / total_trades * 100
    return win_ratio

class TradeRecord(models.Model):
  ticker = models.CharField(max_length=6)
  action = models.CharField(max_length=4)
  execution_price = models.DecimalField(max_digits=12, decimal_places=4)
  pnl = models.DecimalField(max_digits=12, decimal_places=2)
  is_closed = models.BooleanField(default=True)
  account = models.ForeignKey(PropAccount, on_delete=models.CASCADE, related_name="trades")

  @property
  def is_profitable(self) -> bool:
    return self.pnl > 0