from tempfile import TemporaryDirectory

from allauth.account.models import EmailAddress

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import Client, TransactionTestCase, override_settings
from django.urls import reverse

from core.models import (
    BookListing,
    BookSwap,
    Community,
    CommunityMembership,
    CommunityMembershipRequest,
    Genre,
)


class ResetDatabaseCommandTests(TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.temp_media = TemporaryDirectory()
        self.media_override = override_settings(MEDIA_ROOT=self.temp_media.name)
        self.media_override.enable()

    def tearDown(self):
        self.media_override.disable()
        self.temp_media.cleanup()
        super().tearDown()

    def test_reset_database_seeds_local_data(self):
        call_command("reset_database")

        self.assertTrue(
            EmailAddress.objects.filter(
                user__username="admin",
                email="admin@test.com",
                verified=True,
                primary=True,
            ).exists()
        )
        self.assertEqual(Community.objects.count(), 3)
        self.assertEqual(BookListing.objects.count(), 6)
        self.assertEqual(
            BookListing.objects.filter(status=BookListing.Status.PENDING).count(), 1
        )
        self.assertTrue(
            BookSwap.objects.filter(status=BookSwap.Status.ACCEPTED).exists()
        )
        self.assertTrue(
            BookSwap.objects.filter(status=BookSwap.Status.PROPOSED).exists()
        )
        self.assertTrue(
            CommunityMembershipRequest.objects.filter(
                status=CommunityMembershipRequest.Status.PENDING
            ).exists()
        )
        self.assertTrue(Genre.objects.filter(name="Sci-Fi").exists())


class CommunityMembershipTests(TransactionTestCase):
    def test_member_can_leave_community(self):
        user = User.objects.create_user(
            username="reader",
            email="reader@test.com",
            password="password",
        )
        community = Community.objects.create(
            name="Swap Circle",
            description="A local book swap group.",
            created_by=user,
        )
        CommunityMembership.objects.create(user=user, community=community)

        client = Client()
        self.assertTrue(client.login(username="reader", password="password"))

        response = client.post(reverse("leave_community", args=[community.id]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("community", args=[community.id]))
        self.assertFalse(
            CommunityMembership.objects.filter(user=user, community=community).exists()
        )
