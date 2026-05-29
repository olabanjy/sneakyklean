from django.shortcuts import render


def index_view(request):
    """Landing page view."""
    return render(request, 'core/index.html')
