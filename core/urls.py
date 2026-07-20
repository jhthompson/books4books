from django.urls import path

from core import views

urlpatterns = [
    # admin
    path("approve", views.approve_pending_listings, name="approve_pending_listings"),
    # communities
    path("communities", views.communities, name="communities"),
    path("communities/new", views.new_community, name="new_community"),
    path("communities/<int:id>", views.community, name="community"),
    # community membership
    path(
        "communities/<int:id>/join",
        views.join_community,
        name="join_community",
    ),
    # listings
    path("listings", views.listings, name="listings"),
    path("listings/new", views.new_listing, name="new_listing"),
    path(
        "listings/new/isbn",
        views.new_listing_isbn_prompt,
        name="new_listing_isbn_prompt",
    ),
    path(
        "listings/new/isbn/<str:isbn>",
        views.new_listing_from_isbn,
        name="new_listing_from_isbn",
    ),
    path("listings/<int:id>", views.listing, name="listing"),
    path("listings/<int:id>/delete", views.delete_listing, name="delete_listing"),
    # swaps
    path("swaps", views.swaps, name="swaps"),
    path("swaps/new", views.new_swap, name="new_swap"),
    path("swaps/<int:id>", views.swap, name="swap"),
    path("swaps/<int:id>/messages", views.swap_messages, name="swap_messages"),
    path("swaps/<int:id>/cancel", views.cancel_swap, name="cancel_swap"),
    path("swaps/<int:id>/accept", views.accept_swap, name="accept_swap"),
    path("swaps/<int:id>/complete", views.complete_swap, name="complete_swap"),
    path("swaps/<int:id>/decline", views.decline_swap, name="decline_swap"),
    # discovery
    path("search", views.search_communities, name="search"),
    # profile
    path("profile/<int:id>", views.profile, name="profile"),
    path("profile/<int:id>/edit", views.edit_profile, name="edit_profile"),
    # index
    path("", views.index, name="index"),
]
