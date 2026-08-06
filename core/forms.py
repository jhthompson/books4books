from isbn_field.validators import ISBNValidator

from django import forms
from django.core.exceptions import ValidationError

from core.models import BookListing, Community, Genre


class EditProfileForm(forms.Form):
    username = forms.CharField(max_length=150)


class NewCommunityForm(forms.Form):
    name = forms.CharField(max_length=255)
    description = forms.CharField(max_length=1000)
    visibility = forms.ChoiceField(
        choices=Community.Visibility.choices,
        initial=Community.Visibility.PUBLIC,
        help_text=(
            "Public communities are open to all. Private communities require a join "
            "request and admin approval."
        ),
    )


class IsbnForm(forms.Form):
    """
    Get an ISBN from either:

      - barcode: EAN13 barcode image
      - isbn: string
    """

    barcode = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(
            attrs={"capture": "environment", "accept": "image/*"}
        ),
    )

    isbn = forms.CharField(
        required=False,
        label="ISBN",
        min_length=10,
        validators=[ISBNValidator],
    )

    def clean(self):
        cleaned_data = super().clean()
        barcode = cleaned_data.get("barcode")
        isbn = cleaned_data.get("isbn")

        if not barcode and not isbn:
            raise ValidationError(
                "Please provide either an image of the barcode or an ISBN."
            )


class NewBookListingForm(forms.Form):
    # user editable
    title = forms.CharField(max_length=255)
    isbn = forms.CharField(
        label="ISBN",
        max_length=13,
        required=False,
        validators=[ISBNValidator],
    )
    authors = forms.CharField(
        label="Author(s)",
        max_length=255,
        help_text="Separate multiple authors with commas.",
    )
    cover = forms.ImageField(
        label="Picture of the book's cover",
        widget=forms.ClearableFileInput(attrs={"accept": "image/*"}),
    )
    genres = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        choices=[(g, g) for g in Genre.COMMON_GENRES],
    )

    # populated from OpenLibrary API lookup
    openlibrary_author_names = forms.CharField(
        widget=forms.HiddenInput(), max_length=255, required=False
    )
    openlibrary_author_ids = forms.CharField(
        widget=forms.HiddenInput(), max_length=255, required=False
    )
    openlibrary_edition_id = forms.CharField(
        widget=forms.HiddenInput(), max_length=255, required=False
    )
    openlibrary_work_id = forms.CharField(
        widget=forms.HiddenInput(), max_length=255, required=False
    )


class BookListingSelectionFormSet(forms.BaseFormSet):
    def __init__(self, *args, **kwargs):
        self.owners = kwargs.pop("owners", [])
        self.community = kwargs.pop("community")
        super().__init__(*args, **kwargs)

    def get_form_kwargs(self, form_index):
        form_kwargs = super().get_form_kwargs(form_index)
        if form_index < len(self.owners):
            form_kwargs["owner"] = self.owners[form_index]
            form_kwargs["community"] = self.community
            form_kwargs["required"] = form_index == 0
        return form_kwargs


class BookListingSelectionForm(forms.Form):
    book_listings = forms.ModelMultipleChoiceField(
        queryset=BookListing.objects.filter(status=BookListing.Status.AVAILABLE),
        widget=forms.CheckboxSelectMultiple,
        label="Select books",
    )

    def __init__(self, *args, **kwargs):
        owner = kwargs.pop("owner", None)
        community = kwargs.pop("community", None)
        required = kwargs.pop("required", True)
        super().__init__(*args, **kwargs)
        self.fields["book_listings"].required = required
        if owner and community:
            self.fields["book_listings"].queryset = BookListing.objects.filter(
                owner=owner,
                status=BookListing.Status.AVAILABLE,
                communities=community,
            )
            self.fields["book_listings"].label = f"{owner.username}'s books"


class ListingCommunitiesForm(forms.Form):
    communities = forms.ModelMultipleChoiceField(
        label="Listed in",
        queryset=Community.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["communities"].queryset = user.communities.order_by("name")


class JoinPrivateCommunityForm(forms.Form):
    message = forms.CharField(
        label="Introduce yourself",
        widget=forms.Textarea(attrs={"class": "width:100"}),
        required=True,
        help_text=(
            "Explain your connection to the community so the admins can understand "
            "your request."
        ),
    )
