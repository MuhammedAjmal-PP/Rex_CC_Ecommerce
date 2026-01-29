from urllib.parse import urlparse, parse_qs


def get_category_from_referer(request):
    referer = request.META.get("HTTP_REFERER")

    if not referer:
        return None

    parsed_url = urlparse(referer)
    query_params = parse_qs(parsed_url.query)

    category_slug = query_params.get("category")

    if not category_slug:
        return None

    return category_slug[0]
