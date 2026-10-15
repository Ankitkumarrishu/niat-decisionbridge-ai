from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.schemas.dashboard import DashboardAnalytics, ExperimentCohortMetrics, MetricRate


def _rate(numerator: int, denominator: int, label: str) -> MetricRate:
    if denominator <= 0:
        return MetricRate(numerator=numerator, denominator=denominator, rate=None, label=label)
    return MetricRate(
        numerator=numerator,
        denominator=denominator,
        rate=round(numerator / denominator, 4),
        label=label,
    )


def compute_dashboard(
    leads: list[dict[str, Any]],
    brief_count: int,
    date_from: str,
    date_to: str,
    include_demo: bool,
) -> DashboardAnalytics:
    eligible = [l for l in leads if l.get("is_eligible_lead", True) and l.get("consent_storage")]
    notes: list[str] = []

    if include_demo:
        notes.append("Dashboard includes synthetic demo records (is_demo=true).")

    follow_up_requests = sum(1 for l in eligible if l.get("consent_followup"))
    briefs_generated = sum(1 for l in eligible if l.get("brief_generated_at"))
    # cross-check with brief_count from table when available
    briefs_generated = max(briefs_generated, brief_count)

    completed_apps = sum(1 for l in eligible if l.get("application_status") == "completed")

    by_objection: dict[str, int] = {}
    by_lang: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for l in eligible:
        obj = l.get("primary_objection") or l.get("primary_concern") or "unknown"
        by_objection[obj] = by_objection.get(obj, 0) + 1
        lang = l.get("preferred_language") or "unknown"
        by_lang[lang] = by_lang.get(lang, 0) + 1
        st = l.get("follow_up_status") or "unknown"
        by_status[st] = by_status.get(st, 0) + 1

    funnel = [
        {"stage": "Consented leads", "count": len(eligible)},
        {"stage": "Briefs generated", "count": briefs_generated},
        {"stage": "Follow-up requested", "count": follow_up_requests},
        {"stage": "Contacted", "count": sum(1 for l in eligible if l.get("follow_up_status") == "contacted")},
        {
            "stage": "Application completed",
            "count": completed_apps,
        },
    ]

    # Time series by day
    ts_map: dict[str, int] = {}
    for l in eligible:
        day = (l.get("created_at") or "")[:10]
        if day:
            ts_map[day] = ts_map.get(day, 0) + 1
    time_series = [{"date": d, "leads": ts_map[d]} for d in sorted(ts_map.keys())]

    experiment_comparison = _experiment_metrics(eligible, notes)

    return DashboardAnalytics(
        date_from=date_from,
        date_to=date_to,
        total_consented_leads=len(eligible),
        decision_briefs_generated=briefs_generated,
        counsellor_follow_up_requests=follow_up_requests,
        completed_applications=completed_apps,
        leads_by_primary_objection=by_objection,
        leads_by_language=by_lang,
        leads_by_follow_up_status=by_status,
        brief_generation_success_rate=_rate(
            briefs_generated,
            len(eligible),
            "Successfully generated briefs / eligible consented submissions",
        ),
        lead_to_application_conversion_rate=_rate(
            completed_apps,
            len(eligible),
            "Application completed / eligible consented leads in range",
        ),
        counsellor_follow_up_rate=_rate(
            follow_up_requests,
            len(eligible),
            "Follow-up requested / eligible consented leads in range",
        ),
        funnel=funnel,
        time_series=time_series,
        experiment_comparison=experiment_comparison,
        demo_data_included=include_demo,
        notes=notes,
    )


def _experiment_metrics(eligible: list[dict], notes: list[str]) -> list[ExperimentCohortMetrics]:
    groups = ["control", "treatment"]
    out: list[ExperimentCohortMetrics] = []
    now = datetime.now(timezone.utc)

    for group in groups:
        cohort = [l for l in eligible if l.get("experiment_group") == group]
        within_7: int | None = 0
        missing_ts = 0
        window_open = 0
        for l in cohort:
            enrolled_raw = l.get("experiment_enrolled_at") or l.get("created_at")
            completed_raw = l.get("application_completed_at")
            if l.get("application_status") != "completed":
                continue
            if not enrolled_raw or not completed_raw:
                missing_ts += 1
                continue
            enrolled = datetime.fromisoformat(enrolled_raw.replace("Z", "+00:00"))
            completed = datetime.fromisoformat(completed_raw.replace("Z", "+00:00"))
            if (completed - enrolled).days <= 7:
                within_7 += 1
            if (now - enrolled).days < 7:
                window_open += 1

        note_parts = []
        if missing_ts:
            note_parts.append(f"{missing_ts} completed applications missing enrollment/completion timestamps.")
        if window_open:
            note_parts.append(
                f"{window_open} enrollments still within 7-day observation window; rates may change."
            )
        if len(cohort) < 30:
            note_parts.append("Sample size is small; do not infer statistical significance.")
        if not note_parts:
            note_parts.append("7-day application metric uses recorded timestamps only.")

        out.append(
            ExperimentCohortMetrics(
                group=group,
                eligible_leads=len(cohort),
                briefs_generated=sum(1 for l in cohort if l.get("brief_generated_at")),
                follow_up_requests=sum(1 for l in cohort if l.get("consent_followup")),
                applications_completed=sum(1 for l in cohort if l.get("application_status") == "completed"),
                applications_within_7_days=within_7 if cohort else 0,
                applications_within_7_days_note=" ".join(note_parts),
            )
        )

    if not any(l.get("experiment_group") for l in eligible):
        notes.append("No experiment_group assignments found in selected date range.")

    return out
