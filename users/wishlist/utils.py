def get_session_wishlist(request):
    return request.session.get("wishlist", [])


def add_to_session_wishlist(request, variant_id):
    wishlist = get_session_wishlist(request)

    if variant_id not in wishlist:
        wishlist.append(variant_id)
        message = "Added to wishlist ❤️"
    else:
        message = "Already in your wishlist"

    request.session["wishlist"] = wishlist
    request.session.modified = True
    return message


def remove_from_session_wishlist(request, variant_id):
    wishlist = get_session_wishlist(request)

    wishlist = [vid for vid in wishlist if vid != variant_id]

    request.session["wishlist"] = wishlist
    request.session.modified = True
