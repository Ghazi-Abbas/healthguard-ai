
from datetime import date

from app.schemas.eligibility import EligibilityResult


class EligibilityService:

    def evaluate(
        self,
        *,
        member_id: str,
        service_date: str | None,
        coverage_records: list[dict]
    ) -> EligibilityResult:

        # 1. Validate the requested service date.
        if not service_date:
            return EligibilityResult(
                member_id=member_id,
                status="UNKNOWN",
                reason=(
                    "The requested service date is missing. "
                    "Coverage cannot be verified for the relevant date."
                )
            )

        try:
            requested_date = date.fromisoformat(service_date)
        except (ValueError, TypeError):
            return EligibilityResult(
                member_id=member_id,
                status="UNKNOWN",
                reason=(
                    "The requested service date is invalid. "
                    "A valid ISO date (YYYY-MM-DD) is required."
                )
            )

        # 2. Check whether coverage records exist.
        if not coverage_records:
            return EligibilityResult(
                member_id=member_id,
                status="UNKNOWN",
                service_date=requested_date,
                reason=(
                    "No authoritative coverage record was found "
                    "for this member in the organization."
                )
            )

        known_statuses = {
            "ACTIVE",
            "INACTIVE",
            "SUSPENDED"
        }

        parsed_records = []

        # 3. Validate and parse every coverage record.
        for record in coverage_records:

            try:
                status = record["coverage_status"].upper()

                if status not in known_statuses:
                    raise ValueError("Unknown coverage status")

                effective_date = date.fromisoformat(
                    record["effective_date"]
                )

                termination_value = record.get("termination_date")

                termination_date = (
                    date.fromisoformat(termination_value)
                    if termination_value
                    else None
                )

            except (KeyError, ValueError, TypeError, AttributeError):
                return EligibilityResult(
                    member_id=member_id,
                    status="UNKNOWN",
                    service_date=requested_date,
                    reason=(
                        "The authoritative coverage data is incomplete "
                        "or contains an invalid value. "
                        "Manual verification is required."
                    )
                )

            parsed_records.append({
                "status": status,
                "effective_date": effective_date,
                "termination_date": termination_date,
                "plan_id": record.get("plan_id")
            })

        # 4. Check whether any ACTIVE record covers the service date.
        for record in parsed_records:

            active_on_service_date = (
                record["status"] == "ACTIVE"
                and record["effective_date"] <= requested_date
                and (
                    record["termination_date"] is None
                    or requested_date <= record["termination_date"]
                )
            )

            if active_on_service_date:
                return EligibilityResult(
                member_id=member_id,
                status="ELIGIBLE_FOR_REVIEW",
                plan_id=record["plan_id"],
                service_date=requested_date,
                effective_date=record["effective_date"],
                termination_date=record["termination_date"],
                coverage_status=record["status"],
                reason=(
                    "An active coverage record applies "
                    "to the requested service date."
                )
            )

        # 5. No active coverage record applies.
        return EligibilityResult(
            member_id=member_id,
            status="NOT_ELIGIBLE",
            service_date=requested_date,
            reason=(
                "No active coverage record applies to the "
                "requested service date."
            )
        )
