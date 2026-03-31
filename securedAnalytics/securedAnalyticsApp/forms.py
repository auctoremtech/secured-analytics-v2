import re

from django import forms

from .models import Person

US_ZIP_RE = re.compile(r'^\d{5}(-\d{4})?$')
NAME_RE = re.compile(r"^[A-Za-z\s\-'\.]+$")
PHONE_RE = re.compile(r"^\+?1?[\s.\-]?\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}$")
ADDRESS_RE = re.compile(r"^[A-Za-z0-9\s,\.#\-'/]+$")
CITY_RE = re.compile(r"^[A-Za-z0-9\s\-'\.]+$")

US_STATES_CHOICES = [
    ("", "— Select State —"),
    ("AL", "Alabama"),
    ("AK", "Alaska"),
    ("AZ", "Arizona"),
    ("AR", "Arkansas"),
    ("CA", "California"),
    ("CO", "Colorado"),
    ("CT", "Connecticut"),
    ("DE", "Delaware"),
    ("FL", "Florida"),
    ("GA", "Georgia"),
    ("HI", "Hawaii"),
    ("ID", "Idaho"),
    ("IL", "Illinois"),
    ("IN", "Indiana"),
    ("IA", "Iowa"),
    ("KS", "Kansas"),
    ("KY", "Kentucky"),
    ("LA", "Louisiana"),
    ("ME", "Maine"),
    ("MD", "Maryland"),
    ("MA", "Massachusetts"),
    ("MI", "Michigan"),
    ("MN", "Minnesota"),
    ("MS", "Mississippi"),
    ("MO", "Missouri"),
    ("MT", "Montana"),
    ("NE", "Nebraska"),
    ("NV", "Nevada"),
    ("NH", "New Hampshire"),
    ("NJ", "New Jersey"),
    ("NM", "New Mexico"),
    ("NY", "New York"),
    ("NC", "North Carolina"),
    ("ND", "North Dakota"),
    ("OH", "Ohio"),
    ("OK", "Oklahoma"),
    ("OR", "Oregon"),
    ("PA", "Pennsylvania"),
    ("RI", "Rhode Island"),
    ("SC", "South Carolina"),
    ("SD", "South Dakota"),
    ("TN", "Tennessee"),
    ("TX", "Texas"),
    ("UT", "Utah"),
    ("VT", "Vermont"),
    ("VA", "Virginia"),
    ("WA", "Washington"),
    ("WV", "West Virginia"),
    ("WI", "Wisconsin"),
    ("WY", "Wyoming"),
    ("DC", "District of Columbia"),
    ("AS", "American Samoa"),
    ("GU", "Guam"),
    ("MP", "Northern Mariana Islands"),
    ("PR", "Puerto Rico"),
    ("VI", "U.S. Virgin Islands"),
]


class DemographicsForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150)
    middle_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150)
    NAME_SUFFIX_CHOICES = [
        ("", "— None —"),
        ("Jr.", "Jr."),
        ("Sr.", "Sr."),
        ("II", "II"),
        ("III", "III"),
        ("IV", "IV"),
        ("V", "V"),
        ("Esq.", "Esq."),
        ("Ph.D.", "Ph.D."),
        ("M.D.", "M.D."),
        ("J.D.", "J.D."),
        ("D.D.S.", "D.D.S."),
        ("D.O.", "D.O."),
        ("R.N.", "R.N."),
        ("Ret.", "Ret."),
    ]

    name_suffix = forms.ChoiceField(choices=NAME_SUFFIX_CHOICES, required=False)
    state = forms.ChoiceField(choices=US_STATES_CHOICES)

    REQUIRED_DEMOGRAPHICS_FIELDS = (
        "phone_number", "address", "city", "state", "zip_code",
        "date_of_birth", "ethnicity", "gender", "rank", "years_of_service",
    )

    class Meta:
        model = Person
        fields = [
            "first_name",
            "middle_name",
            "last_name",
            "name_suffix",
            "phone_number",
            "address",
            "city",
            "state",
            "zip_code",
            "date_of_birth",
            "ethnicity",
            "gender",
            "rank",
            "years_of_service",
        ]

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

        # Mark model-level fields as required in the form
        for field_name in self.REQUIRED_DEMOGRAPHICS_FIELDS:
            if field_name in self.fields:
                self.fields[field_name].required = True

        source_user = self.user
        if source_user is None and self.instance and self.instance.pk:
            source_user = self.instance.user

        if source_user is not None:
            self.fields["first_name"].initial = source_user.first_name
            self.fields["middle_name"].initial = getattr(source_user, "middle_name", "")
            self.fields["last_name"].initial = source_user.last_name
            self.fields["name_suffix"].initial = getattr(source_user, "name_suffix", "")

        self.fields["zip_code"].widget.attrs.update({
            "pattern": r"\d{5}(-\d{4})?",
            "title": "Enter a valid US zip code (e.g. 12345 or 12345-6789)",
            "placeholder": "12345 or 12345-6789",
        })

        self.fields["date_of_birth"].widget = forms.DateInput(
            attrs={"type": "date"}, format="%Y-%m-%d"
        )

        _name_attrs = {
            "pattern": r"[A-Za-z\s\-'\.]+",
            "title": "Letters, spaces, hyphens, apostrophes, and periods only",
        }
        for _f in ("first_name", "middle_name", "last_name"):
            self.fields[_f].widget.attrs.update(_name_attrs)

        self.fields["phone_number"].widget.attrs.update({
            "pattern": r"\+?1?[\s.\-]?\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}",
            "title": "Enter a valid US phone number (e.g. 555-123-4567)",
            "placeholder": "555-123-4567",
        })

        self.fields["address"].widget.attrs.update({
            "title": "Letters, numbers, spaces, and common punctuation (. , # - ' /) only",
            "placeholder": "123 Main St",
        })

        self.fields["city"].widget.attrs.update({
            "pattern": r"[A-Za-z0-9\s\-'\.]+",
            "title": "Letters, numbers, spaces, hyphens, apostrophes, and periods only",
            "placeholder": "City name",
        })

    def _clean_name_field(self, field_name):
        value = self.cleaned_data.get(field_name, "")
        if value and not NAME_RE.match(value):
            label = field_name.replace("_", " ").title()
            raise forms.ValidationError(
                f"{label} may only contain letters, spaces, hyphens, apostrophes, and periods."
            )
        return value

    def clean_first_name(self):
        return self._clean_name_field("first_name")

    def clean_middle_name(self):
        return self._clean_name_field("middle_name")

    def clean_last_name(self):
        return self._clean_name_field("last_name")

    def clean_phone_number(self):
        value = self.cleaned_data.get("phone_number", "")
        if value and not PHONE_RE.match(value):
            raise forms.ValidationError(
                "Enter a valid US phone number (e.g. 555-123-4567 or (555) 123-4567)."
            )
        return value

    def clean_address(self):
        value = self.cleaned_data.get("address", "")
        if value and not ADDRESS_RE.match(value):
            raise forms.ValidationError(
                "Address may only contain letters, numbers, spaces, and common punctuation (. , # - ' /)."
            )
        return value

    def clean_city(self):
        value = self.cleaned_data.get("city", "")
        if value and not CITY_RE.match(value):
            raise forms.ValidationError(
                "City name may only contain letters, numbers, spaces, hyphens, apostrophes, and periods."
            )
        return value

    def clean_zip_code(self):
        zip_code = self.cleaned_data.get("zip_code", "")
        if zip_code and not US_ZIP_RE.match(zip_code):
            raise forms.ValidationError(
                "Enter a valid US zip code (e.g. 12345 or 12345-6789)."
            )
        return zip_code

    def save(self, commit=True):
        person = super().save(commit=False)
        user = self.user or getattr(person, "user", None)

        if user is None:
            raise ValueError("DemographicsForm.save() requires an associated user.")

        user.first_name = self.cleaned_data["first_name"]
        user.middle_name = self.cleaned_data["middle_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.name_suffix = self.cleaned_data["name_suffix"]
        person.user = user

        if commit:
            user.save()
            person.save()
            self.save_m2m()

        return person