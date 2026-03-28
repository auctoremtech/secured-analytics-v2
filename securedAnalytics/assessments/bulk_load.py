import csv
import io
import logging
import re

from django import forms
from django.contrib import admin, messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import path

from securedAnalyticsApp.models import (
    SLECategory,
    SLEQuestion,
    MERCategory,
    MERQuestion,
    OWBCategory,
    OWBQuestion,
    PSWCategory,
    PSWQuestion,
    OCLCategory,
    OCLQuestion,
)

ASSESSMENT_REGISTRY = {
    "sle": {
        "label": "Supervisor's Leadership Engagement",
        "category_model": SLECategory,
        "question_model": SLEQuestion,
    },
    "mer": {
        "label": "Mental and Emotional Resilience in Leadership",
        "category_model": MERCategory,
        "question_model": MERQuestion,
    },
    "owb": {
        "label": "Officer Wellbeing",
        "category_model": OWBCategory,
        "question_model": OWBQuestion,
    },
    "psw": {
        "label": "Psychological Safety in the Workplace",
        "category_model": PSWCategory,
        "question_model": PSWQuestion,
    },
    "ocl": {
        "label": "Organizational Culture and Leadership Change",
        "category_model": OCLCategory,
        "question_model": OCLQuestion,
    },
}

ASSESSMENT_CHOICES = [("", "— Select Assessment —")] + [
    (key, info["label"]) for key, info in ASSESSMENT_REGISTRY.items()
]

# Matches any standard Roman numeral (I – XXX and beyond) at the start of a line
# followed by a period, then the category title, and an optional parenthesised description.
ROMAN_PATTERN = re.compile(
    r"^(M{0,3}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3}))"
    r"\.\s+(.+?)(?:\s*\((.+)\))?\s*$"
)
QUESTION_PATTERN = re.compile(r"^(\d+)\.\s+(.+)$")


logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".txt", ".csv", ".docx", ".pdf"}


class BulkLoadForm(forms.Form):
    assessment = forms.ChoiceField(choices=ASSESSMENT_CHOICES)
    file = forms.FileField(
        help_text="Upload a Word (.docx), PDF (.pdf), CSV (.csv), or plain-text (.txt) file. "
        "Content should have Roman-numeral headings (e.g. I. Title) followed by numbered questions.",
    )

    def clean_file(self):
        uploaded = self.cleaned_data["file"]
        ext = "." + uploaded.name.rsplit(".", 1)[-1].lower() if "." in uploaded.name else ""
        if ext not in ALLOWED_EXTENSIONS:
            raise forms.ValidationError(
                f"Unsupported file type. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )
        return uploaded


def _parse_text(content):
    """Parse plain-text assessment content into categories and questions."""
    categories = []
    current_category = None

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        roman_match = ROMAN_PATTERN.match(line)
        if roman_match and roman_match.group(1):
            current_category = {
                "numeral": roman_match.group(1),
                "title": roman_match.group(2).strip(),
                "description": (roman_match.group(3) or "").strip(),
                "questions": [],
            }
            categories.append(current_category)
            continue

        q_match = QUESTION_PATTERN.match(line)
        if q_match and current_category is not None:
            q_num = int(q_match.group(1))
            q_text = q_match.group(2).strip()
            current_category["questions"].append({"number": q_num, "text": q_text})

    return categories


def _parse_csv(content):
    """Parse CSV content into categories and questions.

    Expected columns: numeral, title, description, question_number, question_text
    """
    reader = csv.DictReader(io.StringIO(content))
    cat_map = {}
    cat_order = []

    for row in reader:
        numeral = row.get("numeral", "").strip()
        if not numeral:
            continue
        if numeral not in cat_map:
            cat_map[numeral] = {
                "numeral": numeral,
                "title": row.get("title", "").strip(),
                "description": row.get("description", "").strip(),
                "questions": [],
            }
            cat_order.append(numeral)
        q_text = row.get("question_text", "").strip()
        q_num_raw = row.get("question_number", "").strip()
        if q_text:
            q_num = int(q_num_raw) if q_num_raw.isdigit() else None
            cat_map[numeral]["questions"].append({"number": q_num, "text": q_text})

    return [cat_map[n] for n in cat_order]


def _parse_docx(file_obj):
    """Extract text from a .docx file and parse it."""
    import docx

    document = docx.Document(file_obj)
    lines = [para.text for para in document.paragraphs]
    return _parse_text("\n".join(lines))


def _parse_pdf(file_obj):
    """Extract text from a PDF file and parse it."""
    import fitz

    raw_bytes = file_obj.read()
    doc = fitz.open(stream=raw_bytes, filetype="pdf")
    text = "\n".join(page.get_text() for page in doc)
    doc.close()
    return _parse_text(text)


@staff_member_required
def bulk_load_view(request):

    if request.method == "POST":
        form = BulkLoadForm(request.POST, request.FILES)
        if form.is_valid():
            key = form.cleaned_data["assessment"]
            registry = ASSESSMENT_REGISTRY[key]
            CategoryModel = registry["category_model"]
            QuestionModel = registry["question_model"]

            uploaded = request.FILES["file"]
            # Limit file size to 10 MB
            if uploaded.size > 10 * 1024 * 1024:
                messages.error(request, "File too large. Maximum size is 10 MB.")
                return redirect("admin:bulk_load")

            filename = uploaded.name.lower()

            try:
                if filename.endswith(".docx"):
                    categories = _parse_docx(uploaded)
                elif filename.endswith(".pdf"):
                    categories = _parse_pdf(uploaded)
                elif filename.endswith(".csv"):
                    raw = uploaded.read().decode("utf-8")
                    categories = _parse_csv(raw)
                else:
                    raw = uploaded.read().decode("utf-8")
                    categories = _parse_text(raw)
            except UnicodeDecodeError:
                messages.error(request, "File must be UTF-8 encoded text.")
                return redirect("admin:bulk_load")
            except Exception:
                logger.exception("Bulk load file parsing error")
                messages.error(request, "Error reading file. Please check the file format and try again.")
                return redirect("admin:bulk_load")

            if not categories:
                messages.error(
                    request,
                    "No categories found in the file. Check format and try again.",
                )
                return redirect("admin:bulk_load")

            created_cats = 0
            created_qs = 0
            updated_qs = 0
            fallback_number = 1

            with transaction.atomic():
                for order, cat_data in enumerate(categories, start=1):
                    cat, cat_created = CategoryModel.objects.update_or_create(
                        numeral=cat_data["numeral"],
                        defaults={
                            "title": cat_data["title"],
                            "description": cat_data["description"],
                            "order": order,
                        },
                    )
                    if cat_created:
                        created_cats += 1

                    for q_item in cat_data["questions"]:
                        q_num = q_item["number"] if q_item["number"] is not None else fallback_number
                        _, q_created = QuestionModel.objects.update_or_create(
                            number=q_num,
                            defaults={
                                "category": cat,
                                "text": q_item["text"],
                            },
                        )
                        if q_created:
                            created_qs += 1
                        else:
                            updated_qs += 1
                        fallback_number = q_num + 1

            messages.success(
                request,
                f"Loaded {registry['label']}: "
                f"{created_cats} categories created, "
                f"{created_qs} questions created, "
                f"{updated_qs} questions updated.",
            )
            return redirect("admin:bulk_load")
    else:
        form = BulkLoadForm()

    context = {
        **admin.site.each_context(request),
        "title": "Bulk Load Assessment",
        "form": form,
    }
    return render(request, "admin/bulk_load.html", context)


def get_bulk_load_urls():
    return [
        path("bulk-load/", bulk_load_view, name="bulk_load"),
    ]
