"""Organize completed survey responses into per-assessment, per-category
structured records that business logic can iterate and grade."""

from collections import defaultdict

from django.utils import timezone

from assessments.bulk_load import ASSESSMENT_REGISTRY
from .models import AssessmentResult, Person

LIKERT_LABELS = {
    5: "Highly Agree",
    4: "Agree",
    3: "Uncommitted",
    2: "Disagree",
    1: "Highly Disagree",
}


def organize_survey_results(survey_progress):
    """Build and persist :class:`AssessmentResult` records for a completed survey.

    Steps:
        1. Group the flat ``responses`` dict by assessment key → question PK.
        2. Batch-fetch questions (with their categories) from the DB.
        3. Nest questions under their categories, preserving ordering.
        4. Store one :class:`AssessmentResult` per assessment key.

    Returns the list of created/updated ``AssessmentResult`` instances.
    """
    responses = survey_progress.responses or {}
    pool = survey_progress.question_pool or []

    # Resolve the anonymous_id from the Person record
    anon_id = survey_progress.anonymous_id
    if not anon_id:
        try:
            anon_id = Person.objects.values_list(
                "anonymous_id", flat=True,
            ).get(user=survey_progress.user)
            survey_progress.anonymous_id = anon_id
            survey_progress.save(update_fields=["anonymous_id"])
        except Person.DoesNotExist:
            anon_id = ""

    # --- 1. Group (key, pk) pairs present in the pool ----------------------
    pks_by_key: dict[str, list[int]] = defaultdict(list)
    for key, pk in pool:
        pks_by_key[key].append(pk)

    # --- 2. Batch-fetch questions with categories ---------------------------
    fetched: dict[str, dict[int, object]] = {}  # key -> {pk: question_obj}
    for key, pks in pks_by_key.items():
        info = ASSESSMENT_REGISTRY.get(key)
        if not info:
            continue
        qs = (
            info["question_model"]
            .objects
            .filter(pk__in=pks)
            .select_related("category")
            .order_by("category__order", "number")
        )
        fetched[key] = {q.pk: q for q in qs}

    # --- 3. Build nested structure per assessment key -----------------------
    results_to_save: list[AssessmentResult] = []
    now = timezone.now()

    for key, q_map in fetched.items():
        info = ASSESSMENT_REGISTRY.get(key, {})
        label = info.get("label", key.upper())

        # Group questions by category
        cats_map: dict[int, dict] = {}  # category PK -> category dict
        for q in q_map.values():
            cat = q.category
            if cat.pk not in cats_map:
                cats_map[cat.pk] = {
                    "numeral": cat.numeral,
                    "title": cat.title,
                    "description": getattr(cat, "description", ""),
                    "order": cat.order,
                    "questions": [],
                }
            resp_key = f"{key}_{q.pk}"
            raw_answer = responses.get(resp_key, "")
            answer_int = int(raw_answer) if str(raw_answer).isdigit() else None
            cats_map[cat.pk]["questions"].append({
                "pk": q.pk,
                "number": q.number,
                "text": q.text,
                "answer": answer_int,
                "answer_label": LIKERT_LABELS.get(answer_int, "Not Answered"),
            })

        # Sort categories by order, questions by number
        sorted_cats = sorted(cats_map.values(), key=lambda c: c["order"])
        assessment_total = 0
        for cat_dict in sorted_cats:
            cat_dict["questions"].sort(key=lambda q: q["number"])
            cat_score = sum(
                q["answer"] for q in cat_dict["questions"] if q["answer"] is not None
            )
            cat_dict["score"] = cat_score
            assessment_total += cat_score
            del cat_dict["order"]  # internal sort key, not needed in output

        results_to_save.append(AssessmentResult(
            survey_progress=survey_progress,
            assessment_key=key,
            anonymous_id=anon_id,
            assessment_label=label,
            results_data={"categories": sorted_cats},
            score=assessment_total,
            graded_at=now,
        ))

    # Single bulk upsert instead of N individual update_or_create calls
    if results_to_save:
        AssessmentResult.objects.bulk_create(
            results_to_save,
            update_conflicts=True,
            unique_fields=["survey_progress", "assessment_key"],
            update_fields=[
                "anonymous_id", "assessment_label", "results_data",
                "score", "graded_at",
            ],
        )

    return results_to_save
