import json
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from pydantic import BaseModel, Field, ValidationError
from typing import Literal
from .models import PropAccount, TradeRecord

class TradingWebHookSchema(BaseModel):
  ticker: str = Field(pattern=r"^[A-Z0-9]+$")
  action: Literal["BUY", "SELL"]
  price: float = Field(gt=0)
  account_id: str

@csrf_exempt
def tradingview_webhook_gateway(request):
  if request.method != "POST":
    return JsonResponse({"error": "Method not allowed"}, status=405)

  try:
    data = json.loads(request.body)
    validated_trade = TradingWebHookSchema(**data)
  except (json.JSONDecodeError, ValidationError) as e:
    return JsonResponse({"error": "Validation Failed"}, status=400)


  try:
    account = PropAccount.objects.get(account_id=validated_trade.account_id)
  except PropAccount.DoesNotExist:
    return JsonResponse({"error": "Rejected. Account is inactive"}, status=403)

  new_trade = TradeRecord.objects.create(
    account=account,
    ticker=validated_trade.ticker,
    action=validated_trade.action,
    execution_price=Decimal(str(validated_trade.price)),
    pnl=Decimal("150.00"),
    is_closed=True
  )

  account.recalculate_balance_from_trades()
  is_breached = account.check_drawdown_breach()

  return JsonResponse({
    "status": "success",
    "message": f"Signal processed directly by Django. Trade ID: {new_trade.id}",
    "account_health": {
      "balance": str(account.current_balance),
      "is_active": account.is_active,
      "breached": is_breached
    }
  }, status=202)