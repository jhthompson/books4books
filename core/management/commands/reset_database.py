import shutil
from pathlib import Path

from allauth.account.models import EmailAddress

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from core.models import (
    BookListing,
    BookSwap,
    BookSwapEvent,
    BookSwapMessage,
    Community,
    CommunityMembership,
    CommunityMembershipRequest,
    Genre,
)

SAMPLE_PASSWORD = "test"
SAMPLE_COVER_FILES = {
    "human_transit": "TB.jpg",
    "dungeon_crawler_carl": "dungeon-crawler-carl.jpg",
    "funny_story": "funny_story.jpg",
    "intermezzo": "intermezzo.jpg",
    "orbital": "orbital.jpg",
    "left_hand": "cover.jpg",
}


class Command(BaseCommand):
    help = "Flush the database and recreate local development users and sample data."

    def handle(self, *args, **options):
        self.sample_covers = self._load_sample_covers()

        self.stdout.write("Flushing database...")
        call_command("flush", interactive=False, verbosity=0)
        self._reset_media()

        with transaction.atomic():
            self._seed_genres()
            users = self._seed_users()
            communities = self._seed_communities(users)
            listings = self._seed_listings(users, communities)
            self._seed_membership_requests(users, communities)
            self._seed_swaps(users, communities, listings)

        self.stdout.write(self.style.SUCCESS("Database reset complete."))
        self.stdout.write("Superuser: admin / test")
        self.stdout.write("Sample users: alice / test, bob / test, charlie / test")

    def _load_sample_covers(self):
        source_dir = Path(settings.BASE_DIR) / "files" / "media" / "book_listing_covers"
        covers = {}

        for key, filename in SAMPLE_COVER_FILES.items():
            path = source_dir / filename
            if not path.exists():
                raise CommandError(f"Missing sample cover: {path}")
            covers[key] = (filename, path.read_bytes())

        return covers

    def _reset_media(self):
        media_root = Path(settings.MEDIA_ROOT)
        if media_root.exists():
            shutil.rmtree(media_root)
        media_root.mkdir(parents=True, exist_ok=True)

    def _seed_genres(self):
        Genre.objects.bulk_create(
            [Genre(name=name) for name in Genre.COMMON_GENRES],
            ignore_conflicts=True,
        )

    def _seed_users(self):
        return {
            "admin": self._create_user("admin", "admin@test.com", is_superuser=True),
            "alice": self._create_user("alice", "alice@test.com"),
            "bob": self._create_user("bob", "bob@test.com"),
            "charlie": self._create_user("charlie", "charlie@test.com"),
        }

    def _create_user(self, username, email, *, is_superuser=False):
        if is_superuser:
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=SAMPLE_PASSWORD,
            )
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=SAMPLE_PASSWORD,
            )

        EmailAddress.objects.create(
            user=user,
            email=email,
            primary=True,
            verified=True,
        )
        return user

    def _seed_communities(self, users):
        communities = {
            "alta_vista": Community.objects.create(
                name="Alta Vista Books",
                description="General neighborhood swapping.",
                visibility=Community.Visibility.PUBLIC,
                created_by=users["admin"],
            ),
            "rideau": Community.objects.create(
                name="Rideau Readers",
                description="A smaller downtown trading group.",
                visibility=Community.Visibility.PUBLIC,
                created_by=users["alice"],
            ),
            "sci_fi": Community.objects.create(
                name="Sci-Fi Circle",
                description="Private club for speculative fiction fans.",
                visibility=Community.Visibility.PRIVATE,
                created_by=users["bob"],
            ),
        }

        memberships = [
            (
                users["admin"],
                communities["alta_vista"],
                CommunityMembership.PermissionLevel.ADMIN,
            ),
            (
                users["alice"],
                communities["alta_vista"],
                CommunityMembership.PermissionLevel.MEMBER,
            ),
            (
                users["bob"],
                communities["alta_vista"],
                CommunityMembership.PermissionLevel.MEMBER,
            ),
            (
                users["admin"],
                communities["rideau"],
                CommunityMembership.PermissionLevel.MEMBER,
            ),
            (
                users["alice"],
                communities["rideau"],
                CommunityMembership.PermissionLevel.ADMIN,
            ),
            (
                users["bob"],
                communities["sci_fi"],
                CommunityMembership.PermissionLevel.ADMIN,
            ),
        ]

        CommunityMembership.objects.bulk_create(
            [
                CommunityMembership(
                    user=user,
                    community=community,
                    permission_level=permission_level,
                )
                for user, community, permission_level in memberships
            ]
        )

        return communities

    def _seed_listings(self, users, communities):
        return {
            "human_transit": self._create_listing(
                cover_key="human_transit",
                owner=users["admin"],
                title="Human Transit, Revised Edition",
                authors="Jarrett Walker",
                status=BookListing.Status.AVAILABLE,
                communities=[communities["alta_vista"]],
                genres=["Non-Fiction"],
            ),
            "dungeon_crawler_carl": self._create_listing(
                cover_key="dungeon_crawler_carl",
                owner=users["alice"],
                title="Dungeon Crawler Carl",
                authors="Matt Dinniman",
                status=BookListing.Status.AVAILABLE,
                communities=[communities["alta_vista"], communities["rideau"]],
                genres=["Sci-Fi", "Fantasy"],
            ),
            "funny_story": self._create_listing(
                cover_key="funny_story",
                owner=users["bob"],
                title="Funny Story",
                authors="Emily Henry",
                status=BookListing.Status.AVAILABLE,
                communities=[communities["alta_vista"]],
                genres=["Romance", "Fiction"],
            ),
            "intermezzo": self._create_listing(
                cover_key="intermezzo",
                owner=users["bob"],
                title="Intermezzo",
                authors="Sally Rooney",
                status=BookListing.Status.AVAILABLE,
                communities=[communities["alta_vista"]],
                genres=["Literary Fiction"],
            ),
            "orbital": self._create_listing(
                cover_key="orbital",
                owner=users["bob"],
                title="Orbital",
                authors="Samantha Harvey",
                status=BookListing.Status.AVAILABLE,
                communities=[communities["sci_fi"]],
                genres=["Sci-Fi"],
            ),
            "left_hand": self._create_listing(
                cover_key="left_hand",
                owner=users["admin"],
                title="The Left Hand of Darkness",
                authors="Ursula K. Le Guin",
                status=BookListing.Status.PENDING,
                communities=[],
                genres=["Sci-Fi"],
            ),
        }

    def _create_listing(
        self,
        *,
        cover_key,
        owner,
        title,
        authors,
        status,
        communities,
        genres,
    ):
        filename, content = self.sample_covers[cover_key]
        suffix = Path(filename).suffix or ".jpg"

        listing = BookListing.objects.create(
            owner=owner,
            title=title,
            authors=authors,
            status=status,
            cover=ContentFile(
                content,
                name=f"{owner.username}-{slugify(title)}{suffix}",
            ),
        )
        listing.genres.set(Genre.objects.filter(name__in=genres))
        if communities:
            listing.communities.set(communities)
        return listing

    def _seed_membership_requests(self, users, communities):
        CommunityMembershipRequest.objects.create(
            user=users["charlie"],
            community=communities["sci_fi"],
            status=CommunityMembershipRequest.Status.PENDING,
            message="I mostly read space opera and want to join the next swap.",
        )

    def _seed_swaps(self, users, communities, listings):
        accepted_swap = BookSwap.objects.create(
            community=communities["alta_vista"],
            proposed_by=users["bob"],
            proposed_to=users["alice"],
        )
        accepted_swap.offered_listings.set([listings["funny_story"]])
        accepted_swap.requested_listings.set([listings["dungeon_crawler_carl"]])
        BookSwapEvent.objects.create(
            swap=accepted_swap,
            user=users["bob"],
            type=BookSwapEvent.Type.PROPOSE,
        )
        accepted_swap.accept(user=users["alice"])
        BookSwapMessage.objects.create(
            swap=accepted_swap,
            sender=users["bob"],
            content="Works for me — want to trade this weekend?",
        )
        BookSwapMessage.objects.create(
            swap=accepted_swap,
            sender=users["alice"],
            content="Yes, Saturday afternoon is perfect.",
        )

        proposed_swap = BookSwap.objects.create(
            community=communities["alta_vista"],
            proposed_by=users["admin"],
            proposed_to=users["bob"],
        )
        proposed_swap.offered_listings.set([listings["human_transit"]])
        proposed_swap.requested_listings.set([listings["intermezzo"]])
        BookSwapEvent.objects.create(
            swap=proposed_swap,
            user=users["admin"],
            type=BookSwapEvent.Type.PROPOSE,
        )
