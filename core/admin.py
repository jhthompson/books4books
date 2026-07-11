from django.contrib import admin

from core.models import (
    BookListing,
    BookSwap,
    BookSwapEvent,
    BookSwapMessage,
    Community,
    CommunityMembership,
    Genre,
    OpenLibraryAuthor,
)


class CommunityMembershipInline(admin.TabularInline):
    model = CommunityMembership
    extra = 1


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    inlines = [CommunityMembershipInline]


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    pass


@admin.register(OpenLibraryAuthor)
class OpenLibraryAuthorAdmin(admin.ModelAdmin):
    pass


@admin.register(BookListing)
class BookListingAdmin(admin.ModelAdmin):
    pass


class BookSwapEventInline(admin.TabularInline):
    model = BookSwapEvent
    extra = 0


class BookSwapMessageInline(admin.TabularInline):
    model = BookSwapMessage
    extra = 0


@admin.register(BookSwap)
class BookSwapAdmin(admin.ModelAdmin):
    inlines = [BookSwapEventInline, BookSwapMessageInline]
