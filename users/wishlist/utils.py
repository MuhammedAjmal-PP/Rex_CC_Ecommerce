def get_session_wishlist(request):
    return request.session.get("wishlist", [])


def toggle_session_wishlist(request, variant_id):
    wishlist = request.session.get("wishlist", [])

    if variant_id in wishlist:
        wishlist.remove(variant_id)
        message = "Removed from your wishlist"
        added = False
    else:
        wishlist.append(variant_id)
        message = "Added to wishlist ❤️"
        added = True

    request.session["wishlist"] = wishlist
    request.session.modified = True

    return message, added
