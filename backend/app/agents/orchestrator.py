"""
Blood Donor Matching Orchestrator Agent

Uses Claude Opus 4.8 with tool use (manual agentic loop) to orchestrate
the full blood donor matching flow:

  1. Claude calls get_eligible_donors → gets ranked list
  2. Claude calls launch_outreach_wave → triggers async simulation
  3. Claude calls check_fulfillment_status → decides next action
  4. Repeats until fulfilled or all donors exhausted

Tools are implemented here and executed locally; Claude decides when to call them.
"""

import json
import uuid
from datetime import datetime

import anthropic
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.client import get_client
from app.config import settings
from app.models.blood_request import BloodRequest
from app.schemas.blood_request import BloodRequestExtraction
from app.schemas.donor import DonorMatch
from app.services.broadcast import manager
from app.services.matching import get_eligible_donors
from app.services.outreach import run_wave
from app.services.ranking import rank_donors

MODEL = "claude-opus-4-8"
MAX_WAVES = 5


# ─── Tool Definitions (JSON Schema for Claude) ────────────────────────────────

TOOLS: list[anthropic.types.ToolParam] = [
    {
        "name": "get_eligible_donors",
        "description": (
            "Query the database for eligible blood donors matching the required blood group. "
            "Returns a ranked list of donor objects sorted by proximity, eligibility, and response rate. "
            "Call this first to see who is available."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "blood_group": {
                    "type": "string",
                    "description": "Blood group to search for, e.g. 'O+', 'AB-'",
                },
                "hospital_lat": {
                    "type": "number",
                    "description": "Hospital latitude for distance calculation",
                },
                "hospital_lng": {
                    "type": "number",
                    "description": "Hospital longitude for distance calculation",
                },
            },
            "required": ["blood_group", "hospital_lat", "hospital_lng"],
        },
    },
    {
        "name": "launch_outreach_wave",
        "description": (
            "Launch a wave of outreach to a batch of donors. "
            "Donors will be contacted in parallel; responses arrive asynchronously. "
            "Provide the wave_number and the list of donor IDs to contact in this wave. "
            "Use wave_number=1 for the first wave, incrementing for each subsequent wave."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "wave_number": {"type": "integer", "description": "1-based wave number"},
                "donor_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of donor IDs to contact in this wave",
                },
            },
            "required": ["wave_number", "donor_ids"],
        },
    },
    {
        "name": "check_fulfillment_status",
        "description": (
            "Check whether the blood request has been fulfilled. "
            "Returns confirmed donor count vs required units and overall status."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


# ─── Tool Executor ─────────────────────────────────────────────────────────────

class OrchestratorContext:
    """Carries state across the agentic loop for a single blood request."""

    def __init__(
        self,
        db: AsyncSession,
        request: BloodRequest,
        extraction: BloodRequestExtraction,
    ) -> None:
        self.db = db
        self.request = request
        self.extraction = extraction
        self.ranked_donors: list[DonorMatch] = []
        self.contacted_donor_ids: set[str] = set()
        self.wave_count: int = 0

    async def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        if tool_name == "get_eligible_donors":
            return await self._get_eligible_donors(tool_input)
        if tool_name == "launch_outreach_wave":
            return await self._launch_outreach_wave(tool_input)
        if tool_name == "check_fulfillment_status":
            return await self._check_fulfillment_status()
        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    async def _get_eligible_donors(self, inp: dict) -> str:
        eligible = await get_eligible_donors(
            self.db,
            blood_group=inp["blood_group"],
        )
        self.ranked_donors = rank_donors(
            eligible,
            hospital_lat=inp["hospital_lat"],
            hospital_lng=inp["hospital_lng"],
        )
        # Filter out already-contacted donors
        fresh = [d for d in self.ranked_donors if d.id not in self.contacted_donor_ids]

        return json.dumps({
            "total_eligible": len(self.ranked_donors),
            "available_for_outreach": len(fresh),
            "top_donors": [
                {
                    "id": d.id,
                    "name": d.name,
                    "area": d.area,
                    "blood_group": d.blood_group,
                    "distance_km": d.distance_km,
                    "score": d.score,
                }
                for d in fresh[:settings.wave_size * 2]  # Show 2 waves worth
            ],
        })

    async def _launch_outreach_wave(self, inp: dict) -> str:
        wave_number: int = inp["wave_number"]
        donor_ids: list[str] = inp["donor_ids"]

        if self.wave_count >= MAX_WAVES:
            return json.dumps({"error": "Maximum wave limit reached."})

        # Resolve donor objects
        id_set = set(donor_ids)
        wave_donors = [d for d in self.ranked_donors if d.id in id_set]

        if not wave_donors:
            return json.dumps({"error": "No valid donors found for given IDs."})

        self.contacted_donor_ids.update(donor_ids)
        self.wave_count += 1

        # Update request status to in_progress on first wave
        if self.request.status == "pending":
            self.request.status = "in_progress"
            await self.db.commit()

        counts = await run_wave(self.db, self.request, wave_number, wave_donors)
        await self.db.refresh(self.request)

        return json.dumps({
            "wave_number": wave_number,
            "contacted": len(wave_donors),
            "results": counts,
            "confirmed_so_far": self.request.confirmed_donors,
            "units_needed": self.request.units_needed,
            "fulfilled": self.request.confirmed_donors >= self.request.units_needed,
        })

    async def _check_fulfillment_status(self) -> str:
        await self.db.refresh(self.request)
        fulfilled = self.request.confirmed_donors >= self.request.units_needed
        remaining_donors = [
            d for d in self.ranked_donors if d.id not in self.contacted_donor_ids
        ]
        return json.dumps({
            "confirmed_donors": self.request.confirmed_donors,
            "units_needed": self.request.units_needed,
            "fulfilled": fulfilled,
            "remaining_eligible_donors": len(remaining_donors),
            "waves_launched": self.wave_count,
            "max_waves": MAX_WAVES,
        })


# ─── Main Orchestrator Entry Point ─────────────────────────────────────────────

async def run_matching_orchestrator(
    db: AsyncSession,
    request: BloodRequest,
    extraction: BloodRequestExtraction,
) -> None:
    """
    Full agentic loop — runs as a background task after the chat endpoint responds.
    Claude drives the matching flow using tools; results stream via WebSocket.
    """
    client = get_client()
    ctx = OrchestratorContext(db=db, request=request, extraction=extraction)

    system_prompt = f"""You are an intelligent blood donor matching coordinator for an emergency medical system in Karachi.

Your goal is to fulfil the following blood request as quickly as possible:
- Blood Group: {extraction.blood_group}
- Units Needed: {extraction.units_needed}
- Hospital: {extraction.hospital_name}, {extraction.hospital_area}
- Urgency: {extraction.urgency_level}
- Patient: {extraction.patient_name or 'Unknown'}

You have three tools available:
1. get_eligible_donors — find and rank available donors
2. launch_outreach_wave — contact a batch of donors
3. check_fulfillment_status — check if the request is fulfilled

Strategy:
- Start by calling get_eligible_donors to see who is available.
- Launch Wave 1 with the top {settings.wave_size} highest-scored donors.
- After the wave completes, check fulfillment status.
- If not yet fulfilled and more donors are available, launch the next wave.
- Stop when either: (a) confirmed_donors >= units_needed, or (b) no more eligible donors, or (c) max waves reached.
- Be decisive — minimize idle time between waves in emergencies.
"""

    messages: list[anthropic.types.MessageParam] = [
        {
            "role": "user",
            "content": f"Blood request created. Request ID: {request.id}. Please begin the donor matching process now.",
        }
    ]

    await manager.broadcast({
        "event": "status_update",
        "request_id": request.id,
        "wave_number": None,
        "data": {"message": "Orchestrator started. Searching for eligible donors..."},
    })

    # Agentic loop
    while True:
        response = await client.messages.create(
            model=MODEL,
            max_tokens=2048,
            thinking={"type": "adaptive"},
            system=system_prompt,
            tools=TOOLS,
            messages=messages,
        )

        # Append assistant response to history
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            # Claude finished — determine final status
            await db.refresh(request)
            if request.confirmed_donors >= request.units_needed:
                request.status = "fulfilled"
                event = "request_fulfilled"
            else:
                request.status = "failed"
                event = "request_failed"
            await db.commit()

            await manager.broadcast({
                "event": event,
                "request_id": request.id,
                "wave_number": None,
                "data": {
                    "confirmed_donors": request.confirmed_donors,
                    "units_needed": request.units_needed,
                    "total_waves": ctx.wave_count,
                },
            })
            break

        if response.stop_reason != "tool_use":
            break

        # Execute all tool calls in this response
        tool_results: list[anthropic.types.ToolResultBlockParam] = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            result_json = await ctx.execute_tool(block.name, block.input)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result_json,
            })

        messages.append({"role": "user", "content": tool_results})
