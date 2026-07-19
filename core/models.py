import logging

from isbn_field import ISBNField

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.db import models
from django.db.models import Q
from django.forms import ValidationError
from django.http import HttpRequest
from django.template.loader import render_to_string
from django.urls import reverse

logger = logging.getLogger(__name__)


class Community(models.Model):
    class Meta:
        verbose_name_plural = "Communities"

    class Visibility(models.TextChoices):
        PUBLIC = "PUBLIC", "Public"
        PRIVATE = "PRIVATE", "Private"

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    visibility = models.CharField(
        max_length=10,
        choices=Visibility,
        default=Visibility.PUBLIC,
    )

    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    members = models.ManyToManyField(
        User, through="CommunityMembership", related_name="communities"
    )

    def __str__(self):
        return self.name


class CommunityMembership(models.Model):
    class PermissionLevel(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        MEMBER = "MEMBER", "Member"

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    permission_level = models.CharField(
        max_length=10,
        choices=PermissionLevel,
        default=PermissionLevel.MEMBER,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "community"], name="unique_user_community"
            )
        ]


class CommunityBookListing(models.Model):
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    book_listing = models.ForeignKey("BookListing", on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["community", "book_listing"],
                name="unique_community_book_listing",
            )
        ]


class OpenLibraryAuthor(models.Model):
    class Meta:
        verbose_name = "OpenLibrary author"
        verbose_name_plural = "OpenLibrary authors"

    name = models.CharField(max_length=255)
    openlibrary_author_id = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="OpenLibrary Author ID",
    )

    def __str__(self):
        return self.name


class Genre(models.Model):
    COMMON_GENRES = [
        # top-level genres
        "Fiction",
        "Non-Fiction",
        "Young Adult",
        "Children",
        # fiction sub-genres
        "Romance",
        "Sci-Fi",
        "Fantasy",
        "Thrillers",
        "Mystery & Suspense",
        "Manga",
        "Literary Fiction",
        "Historical Fiction",
        "Horror",
        "Graphic Novels",
        "Poetry",
        # non-fiction sub-genres
        "Biography & Memoir",
        "Business",
        "Cookbooks",
        "Colouring Books",
        "Faith & Spirituality",
        "Health",
        "History & Politics",
        "Music, Movies & Performing Arts",
        "Parenting & Family Relationships",
        "Science & Nature",
        "Self-Help & Wellness",
    ]

    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class BookListing(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        AVAILABLE = "AVAILABLE", "Available"
        SWAPPED = "SWAPPED", "Swapped"
        REMOVED = "REMOVED", "Removed"

    # main data
    title = models.CharField(max_length=255)
    isbn = ISBNField(null=True, blank=True)
    authors = models.CharField(max_length=255)
    cover = models.ImageField(upload_to="book_listing_covers/")
    genres = models.ManyToManyField(Genre, blank=True)

    # metadata
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=9,
        choices=Status,
        default=Status.PENDING,
    )
    communities = models.ManyToManyField(
        Community, through="CommunityBookListing", related_name="listings"
    )

    # OpenLibrary data (if available)
    openlibrary_edition_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="OpenLibrary Edition ID",
    )
    openlibrary_work_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="OpenLibrary Work ID",
    )
    openlibrary_authors = models.ManyToManyField(
        OpenLibraryAuthor,
        blank=True,
        verbose_name="OpenLibrary Authors",
    )

    def __str__(self):
        return self.title

    def remove(self):
        if self.status not in [self.Status.AVAILABLE, self.Status.PENDING]:
            raise ValidationError(
                f"Cannot change listing status from {self.status} to {self.Status.REMOVED}."  # noqa: E501
            )

        self.status = self.Status.REMOVED
        self.save(update_fields=["status"])

    def approve(self):
        if self.status != self.Status.PENDING:
            raise ValidationError(
                f"Cannot change listing status from {self.status} to {self.Status.AVAILABLE}."  # noqa: E501
            )

        self.status = self.Status.AVAILABLE
        self.save(update_fields=["status"])


class BookSwap(models.Model):
    #       User (A) proposes a swap to User (B)
    #       System (S) performs automatic actions
    #
    #       ┌─────────PROPOSED────────────┬────────────┐
    #       │            │                │            │
    #       A            B                S            B
    #       │            │                │            │
    #       ▼            ▼                ▼            ▼
    #   CANCELLED     ACCEPTED───S───►RESCINDED    DECLINED
    #                    │
    #                    A
    #                    │
    #                    ▼
    #                COMPLETED

    class Status(models.TextChoices):
        PROPOSED = "PROPOSED", "Proposed"
        CANCELLED = "CANCELLED", "Cancelled"
        RESCINDED = "RESCINDED", "Rescinded"
        ACCEPTED = "ACCEPTED", "Accepted"
        COMPLETED = "COMPLETED", "Completed"
        DECLINED = "DECLINED", "Declined"

    proposed_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="proposed_by"
    )
    proposed_to = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="proposed_to"
    )

    offered_listings = models.ManyToManyField(
        BookListing, related_name="offered_listings"
    )
    requested_listings = models.ManyToManyField(
        BookListing, related_name="requested_listings"
    )

    status = models.CharField(max_length=9, choices=Status, default=Status.PROPOSED)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.proposed_by} proposed a swap to {self.proposed_to} on {self.created_at}"  # noqa: E501

    def get_absolute_url(self):
        return reverse("swap", kwargs={"id": self.pk})

    def notify(self, request: HttpRequest, event_type: "BookSwapEvent.Type"):
        match event_type:
            case BookSwapEvent.Type.PROPOSE:
                subject = f"{self.proposed_by.username} wants to swap books with you"
                message = render_to_string(
                    "core/emails/proposed_swap_notification.txt",
                    {
                        "proposed_by": self.proposed_by,
                        "swap_url": request.build_absolute_uri(self.get_absolute_url()),
                        "offered_listings": self.offered_listings.all(),
                        "requested_listings": self.requested_listings.all(),
                    },
                )
                recipient = self.proposed_to

                send_mail(
                    subject=subject,
                    message=message,
                    from_email=None,
                    recipient_list=[recipient.email],
                )

            case BookSwapEvent.Type.CANCEL:
                pass
            case BookSwapEvent.Type.ACCEPT:
                subject = f"{self.proposed_to.username} accepted your book swap"
                message = render_to_string(
                    "core/emails/accepted_swap_notification.txt",
                    {
                        "proposed_to": self.proposed_to,
                        "swap_url": request.build_absolute_uri(self.get_absolute_url()),
                        "offered_listings": self.offered_listings.all(),
                        "requested_listings": self.requested_listings.all(),
                    },
                )
                recipient = self.proposed_by

                send_mail(
                    subject=subject,
                    message=message,
                    from_email=None,
                    recipient_list=[recipient.email],
                )
            case BookSwapEvent.Type.DECLINE:
                pass

    def accept(self, user: User):
        if user != self.proposed_to:
            raise PermissionDenied("Only the receiver can accept this swap")

        if self.status != self.Status.PROPOSED:
            raise ValidationError(
                f"Cannot change swap status from {self.status} to {self.Status.ACCEPTED}."  # noqa: E501
            )

        self.status = self.Status.ACCEPTED
        self.save()

        BookSwapEvent.objects.create(
            swap=self,
            user=user,
            type=BookSwapEvent.Type.ACCEPT,
        )

    def complete(self, user: User):
        logger.debug("User %s attempting to complete swap %d", user, self.id)

        if user != self.proposed_by:
            raise PermissionDenied("Only the proposer can complete this swap")

        if self.status != self.Status.ACCEPTED:
            raise ValidationError(
                f"Cannot change swap status from {self.status} to {self.Status.COMPLETED}."  # noqa: E501
            )

        self.status = self.Status.COMPLETED
        self.save()

        BookSwapEvent.objects.create(
            swap=self,
            user=user,
            type=BookSwapEvent.Type.COMPLETE,
        )

        # mark all involved books as swapped
        for offered_listing in self.offered_listings.all():
            offered_listing.status = BookListing.Status.SWAPPED
            offered_listing.save()

        for requested_listing in self.requested_listings.all():
            requested_listing.status = BookListing.Status.SWAPPED
            requested_listing.save()

        # cancel any other swaps involving these listings
        book_in_swap = Q(offered_listings__in=self.offered_listings.all()) | Q(
            requested_listings__in=self.requested_listings.all()
        )
        swap_open = Q(status=BookSwap.Status.PROPOSED) | Q(
            status=BookSwap.Status.ACCEPTED
        )
        other_swaps = BookSwap.objects.filter(book_in_swap, swap_open).exclude(
            id=self.id
        )

        for swap in other_swaps:
            try:
                swap.rescind()
                logger.info(
                    "Rescinded swap %d due to completion of swap %d",
                    swap.id,
                    self.id,
                )
            except ValidationError:
                logger.warning(
                    "Failed to rescind swap %d during completion of swap %d",
                    swap.id,
                    self.id,
                )

    def rescind(self):
        if self.status not in [self.Status.PROPOSED, self.Status.ACCEPTED]:
            raise ValidationError(
                f"Cannot change swap status from {self.status} to {self.Status.RESCINDED}."  # noqa: E501
            )

        self.status = self.Status.RESCINDED
        self.save()

        BookSwapEvent.objects.create(
            swap=self,
            user=None,
            type=BookSwapEvent.Type.RESCIND,
        )

    def decline(self, user: User):
        if user != self.proposed_to:
            raise PermissionDenied("Only the receiver can decline this swap")

        if self.status != self.Status.PROPOSED:
            raise ValidationError(
                f"Cannot change swap status from {self.status} to {self.Status.DECLINED}."  # noqa: E501
            )

        self.status = self.Status.DECLINED
        self.save()

        BookSwapEvent.objects.create(
            swap=self,
            user=user,
            type=BookSwapEvent.Type.DECLINE,
        )

    def cancel(self, user: User):
        if user != self.proposed_by:
            raise PermissionDenied("Only the proposer can cancel this swap")

        if self.status != self.Status.PROPOSED:
            raise ValidationError(
                f"Cannot change swap status from {self.status} to {self.Status.CANCELLED}."  # noqa: E501
            )

        self.status = self.Status.CANCELLED
        self.save()

        BookSwapEvent.objects.create(
            swap=self,
            user=user,
            type=BookSwapEvent.Type.CANCEL,
        )

    def get_timeline(self):
        events = [{"type": "event", "item": event} for event in self.events.all()]
        messages = [{"type": "message", "item": msg} for msg in self.messages.all()]

        timeline = events + messages
        timeline.sort(key=lambda x: x["item"].created_at)

        return timeline


class BookSwapEvent(models.Model):
    class Type(models.TextChoices):
        PROPOSE = "PROPOSE", "Proposed"
        CANCEL = "CANCEL", "Cancelled"
        RESCIND = "RESCIND", "Rescinded"
        ACCEPT = "ACCEPT", "Accepted"
        DECLINE = "DECLINE", "Declined"
        COMPLETE = "COMPLETE", "Completed"

    swap = models.ForeignKey(BookSwap, on_delete=models.CASCADE, related_name="events")
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    type = models.CharField(max_length=8, choices=Type)
    created_at = models.DateTimeField(auto_now_add=True)


class BookSwapMessage(models.Model):
    swap = models.ForeignKey(
        BookSwap, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        # Validate that the sender is involved in the swap
        if self.sender != self.swap.proposer and self.sender != self.swap.receiver:
            raise ValidationError("Messages can only be sent by swap participants")
