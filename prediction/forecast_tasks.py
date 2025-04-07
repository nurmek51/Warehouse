from celery import shared_task
from django.db.models import Sum, F
from django.utils import timezone
from datetime import timedelta\

@shared_task
def forecast_by_category():
    from store.models import StoreItem
    categories = StoreItem.objects.exclude(category__isnull=True).values_list('category', flat=True).distinct()
    results = {}
    for cat in categories:
        stock_data = StoreItem.objects.filter(category=cat, status='warehouse').aggregate(total=Sum('quantity'))
        current_stock = stock_data.get('total') or 0

        start_date = timezone.now().date() - timedelta(days=30)
        sales_data = StoreItem.objects.filter(category=cat, status='sold', added_at__date__gte=start_date).aggregate(total=Sum('quantity'))
        historical_sales = sales_data.get('total') or 0

        avg_daily_sales = historical_sales / 30 if historical_sales else 0
        forecast_next_week = avg_daily_sales * 7
        recommended_order = max(0, int(forecast_next_week - current_stock))

        sold_items = StoreItem.objects.filter(category=cat, status='sold', added_at__date__gte=start_date)
        revenue_data = sold_items.aggregate(total_revenue=Sum(F('price') * F('quantity')))
        forecast_revenue = revenue_data.get('total_revenue') or 0

        results[cat] = {
            "current_stock": current_stock,
            "historical_sales": historical_sales,
            "average_daily_sales": avg_daily_sales,
            "forecast_next_week": forecast_next_week,
            "recommended_order": recommended_order,
            "forecast_revenue": float(forecast_revenue)
        }
    return results
