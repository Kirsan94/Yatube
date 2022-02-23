from django.utils import timezone


def year(request):
    today = timezone.now()  # использование временных зон
    return {
        'year': today.year
    }
