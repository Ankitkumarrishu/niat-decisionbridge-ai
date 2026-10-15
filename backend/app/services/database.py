from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from supabase import Client, create_client

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    pass


def _run(operation: str, fn):
    try:
        return fn()
    except DatabaseError:
        raise
    except Exception as exc:
        logger.exception("Supabase %s failed", operation)
        raise DatabaseError(f"Database {operation} failed. Check schema, RLS, and service-role configuration.") from exc


class DatabaseService:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._client: Client | None = None

    @property
    def client(self) -> Client:
        if not self.settings.supabase_configured():
            raise DatabaseError("Supabase is not configured")
        if self._client is None:
            self._client = create_client(
                self.settings.supabase_url,  # type: ignore[arg-type]
                self.settings.supabase_service_role_key,  # type: ignore[arg-type]
            )
        return self._client

    def is_configured(self) -> bool:
        return self.settings.supabase_configured()

    def create_lead(self, payload: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        row = {
            **payload,
            "consent_storage_at": now if payload.get("consent_storage") else None,
            "consent_followup_at": now if payload.get("consent_followup") else None,
        }
        result = _run("lead insert", lambda: self.client.table("leads").insert(row).execute())
        if not result.data:
            raise DatabaseError("Failed to create lead")
        return result.data[0]

    def get_lead(self, lead_id: str) -> Optional[dict[str, Any]]:
        result = _run(
            "lead fetch",
            lambda: self.client.table("leads").select("*").eq("id", lead_id).limit(1).execute(),
        )
        return result.data[0] if result.data else None

    def update_lead(self, lead_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        result = _run(
            "lead update",
            lambda: self.client.table("leads").update(updates).eq("id", lead_id).execute(),
        )
        if not result.data:
            raise DatabaseError("Lead not found or update failed")
        return result.data[0]

    def insert_brief(self, brief: dict[str, Any]) -> dict[str, Any]:
        result = _run("brief insert", lambda: self.client.table("decision_briefs").insert(brief).execute())
        if not result.data:
            raise DatabaseError("Failed to save decision brief")
        return result.data[0]

    def get_brief(self, brief_id: str) -> Optional[dict[str, Any]]:
        result = _run(
            "brief fetch",
            lambda: self.client.table("decision_briefs").select("*").eq("id", brief_id).limit(1).execute(),
        )
        return result.data[0] if result.data else None

    def get_brief_for_lead(self, lead_id: str) -> Optional[dict[str, Any]]:
        lead = self.get_lead(lead_id)
        if not lead or not lead.get("latest_decision_brief_id"):
            return None
        return self.get_brief(lead["latest_decision_brief_id"])

    def insert_event(self, lead_id: str, event_type: str, payload: dict, created_by: str | None = None):
        row = {
            "id": str(uuid4()),
            "lead_id": lead_id,
            "event_type": event_type,
            "payload": payload,
            "created_by": created_by,
        }
        _run("event insert", lambda: self.client.table("lead_events").insert(row).execute())

    def list_leads(
        self,
        search: str | None = None,
        concern: str | None = None,
        language: str | None = None,
        follow_up_status: str | None = None,
        application_status: str | None = None,
        include_demo: bool = True,
    ) -> list[dict[str, Any]]:
        query = self.client.table("leads").select("*").order("created_at", desc=True)
        if not include_demo:
            query = query.eq("is_demo", False)
        if concern:
            query = query.eq("primary_concern", concern)
        if language:
            query = query.eq("preferred_language", language)
        if follow_up_status:
            query = query.eq("follow_up_status", follow_up_status)
        if application_status:
            query = query.eq("application_status", application_status)
        result = _run("lead list", query.execute)
        items = result.data or []
        if search:
            s = search.lower()
            items = [
                l
                for l in items
                if s in (l.get("student_first_name") or "").lower()
                or s in (l.get("email") or "").lower()
            ]
        return items

    def list_events(self, lead_id: str) -> list[dict[str, Any]]:
        result = _run(
            "event list",
            lambda: self.client.table("lead_events")
            .select("*")
            .eq("lead_id", lead_id)
            .order("created_at", desc=True)
            .execute(),
        )
        return result.data or []

    def search_knowledge(self, query_text: str, limit: int = 8) -> list[dict[str, Any]]:
        def verified(limit_n: int = limit):
            return (
                self.client.table("knowledge_documents")
                .select("*")
                .eq("verification_status", "verified")
                .limit(limit_n)
                .execute()
            )

        q = "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in (query_text or "")).strip()
        if not q:
            result = _run("knowledge list", verified)
            return result.data or []

        tokens = [t for t in q.lower().split() if len(t) > 2][:6]
        collected: dict[str, dict] = {}
        try:
            for token in tokens or [q[:40]]:
                p = f"%{token}%"
                r = (
                    self.client.table("knowledge_documents")
                    .select("*")
                    .eq("verification_status", "verified")
                    .or_(f"title.ilike.{p},content.ilike.{p},category.ilike.{p}")
                    .limit(limit)
                    .execute()
                )
                for doc in r.data or []:
                    collected[doc["id"]] = doc
            if collected:
                return list(collected.values())[:limit]
        except Exception:
            logger.exception("Knowledge keyword search failed; returning verified documents")

        result = _run("knowledge fallback", verified)
        return result.data or []

    def fetch_leads_for_analytics(
        self, date_from: str, date_to: str, include_demo: bool = True
    ) -> list[dict[str, Any]]:
        query = (
            self.client.table("leads")
            .select("*")
            .gte("created_at", date_from)
            .lte("created_at", date_to)
        )
        if not include_demo:
            query = query.eq("is_demo", False)
        result = _run("analytics fetch", query.execute)
        return result.data or []

    def count_briefs(self, date_from: str, date_to: str) -> int:
        result = _run(
            "brief count",
            lambda: self.client.table("decision_briefs")
            .select("id", count="exact")
            .eq("generation_status", "success")
            .gte("created_at", date_from)
            .lte("created_at", date_to)
            .execute(),
        )
        return result.count or 0


def get_db() -> DatabaseService:
    return DatabaseService()
