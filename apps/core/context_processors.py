from .navigation import get_sidebar_items


def navigation(request):
    return {
        "sidebar_items": get_sidebar_items(request.user),
    }