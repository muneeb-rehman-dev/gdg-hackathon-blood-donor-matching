"""
Blood Donor Matching Orchestrator Agent — Gemini Function Calling

Uses Gemini with function calling (tool use) to orchestrate the full
blood donor matching flow. Gemini decides when to call each tool;
we execute them locally and return results.
"""

import json
from datetime import datetime

import google.generativeai as genai
from google.generativeai.protos import FunctionResponse, Part
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

MODEL = "gemini-2.0-flash"
MAX_WAVES = 5


# ─── Tool Definitions ─────────────────────────────────────────────────────────

GET_ELIGIBLE_DONORS_DECL = genai.protos.FunctionDeclaration(
    name="get_eligible_donors",
    description=(
        "Query the database for eligible blood donors matching the required blood group. "
        "Returns a ranked list sorted by proximity, eligibility, and response rate. "
        "Call this first to see who is available."
    ),
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "blood_group": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="Blood group e.g. 'O+', 'AB-'",
            ),
            "hospital_lat": genai.protos.Schema(
                type=genai.protos.Type.NUMBER,
                description="Hospital latitude",
            ),
            "hospital_lng": genai.protos.Schema(
                type=genai.protos.Type.NUMBER,
                description="Hospital longitude",
            ),
        },
        required=["blood_group", "hospital_lat", "hospital_lng"],
    ),
)

LAUNCH_OUTREACH_WAVE_DECL = genai.protos.FunctionDeclaration(
    name="launch_outreach_wave",
    description=(
        "Launch a wave of outreach to a batch of donors. "
        "Donors are contacted in parallel; responses arrive asynchronously. "
        "Use wave_number=1 for the first wave, incrementing each time."
    ),
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "wave_number": genai.protos.Schema(
                type=genai.protos.Type.INTEGER,
                description="1-based wave number",
            ),
            "donor_ids": genai.protos.Schema(
                type=genai.protos.Type.ARRAY,
                items=genai.protos.Schema(type=genai.protos.Type.STRING),
                description="List of donor IDs to contact",
            ),
        },
        required=["wave_number", "donor_ids"],
    ),
)

CHECK_FULFILLMENT_DECL = genai.protos.FunctionDeclaration(
    name="check_fulfillment_status",
    description="Check whether the blood request has been fulfilled. Returns confirmed count vs required.",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={},
    ),
)

TOOLS = [genai.protos.Tool(function_declarations=[
    GET_ELIGIBLE_DONORS_DECL,
    LAUNCH_OUTREACH_WAVE_DECL,
    CHECK_FULFILLMENT_DECL,
])]


# ─── Orchestrator Context ──────────────────────────────────────────────────────

class OrchestratorContext:
    def __init__(self, db: AsyncSession, request: BloodRequest, extraction: BloodRequestExtraction):
        self.db = db
        self.request = request
        self.extraction = extraction
        self.ranked_donors: list[DonorMatch] = []
        self.contacted_donor_ids: set[str] = set()
        self.wave_count: int = 0

    async def execute_tool(self, name: str, args: dict) -> str:
        if name == "get_eligible_donors":
            return await self._get_eligible_donors(args)
        if name == "launch_outreach_wave":
            return await self._launch_outreach_wave(args)
        if name == "check_fulfillment_status":
            return await self._check_fulfillment_status()
        return json.dumps({"error": f"Unknown tool: {name}"})

    async def _get_eligible_donors(self, inp: dict) -> str:
        eligible = await get_eligible_donors(self.db, blood_group=inp["blood_group"])
        self.ranked_donors = rank_donors(
            eligible,
            hospital_lat=inp["hospital_lat"],
            hospital_lng=inp["hospital_lng"],
        )
        fresh = [d for d in self.ranked_donors if d.id not in self.contacted_donor_ids]
        return json.dumps({
            "total_eligible": len(self.ranked_donors),
            "available_for_outreach": len(fresh),
            "top_donors": [
                {"id": d.id, "name": d.name, "area": d.area,
                 "blood_group": d.blood_group, "distance_km": d.distance_km, "score": d.score}
                for d in fresh[:settings.wave_size * 2]
            ],
        })

    async def _launch_outreach_wave(self, inp: dict) -> str:
        if self.wave_count >= MAX_WAVES:
            return json.dumps({"error": "Maximum wave limit reached."})

        id_set = set(inp["donor_ids"])
        wave_donors = [d for d in self.ranked_donors if d.id in id_set]

        if not wave_donors:
            return json.dumps({"error": "No valid donors found for given IDs."})

        self.contacted_donor_ids.update(inp["donor_ids"])
        self.wave_count += 1

        if self.request.status == "pending":
            self.request.status = "in_progress"
            await self.db.commit()

        counts = await run_wave(self.db, self.request, inp["wave_number"], wave_donors)
        await self.db.refresh(self.request)

        return json.dumps({
            "wave_number": inp["wave_number"],
            "contacted": len(wave_donors),
            "results": counts,
            "confirmed_so_far": self.request.confirmed_donors,
            "units_needed": self.request.units_needed,
            "fulfilled": self.request.confirmed_donors >= self.request.units_needed,
        })

    async def _check_fulfillment_status(self) -> str:
        await self.db.refresh(self.request)
        remaining = [d for d in self.ranked_donors if d.id not in self.contacted_donor_ids]
        return json.dumps({
            "confirmed_donors": self.request.confirmed_donors,
            "units_needed": self.request.units_needed,
            "fulfilled": self.request.confirmed_donors >= self.request.units_needed,
            "remaining_eligible_donors": len(remaining),
            "waves_launched": self.wave_count,
            "max_waves": MAX_WAVES,
        })


# ─── Main Entry Point ──────────────────────────────────────────────────────────

async def run_matching_orchestrator(
    db: AsyncSession,
    request: BloodRequest,
    extraction: BloodRequestExtraction,
) -> None:
    get_client()
    ctx = OrchestratorContext(db=db, request=request, extraction=extraction)

    system_instruction = f"""You are a blood donor matching coordinator for an emergency system in Karachi.

Blood Request Details:
- Blood Group: {extraction.blood_group}
- Units Needed: {extraction.units_needed}
- Hospital: {extraction.hospital_name}, {extraction.hospital_area}
- Urgency: {extraction.urgency_level}
- Patient: {extraction.patient_name or 'Unknown'}

Strategy:
1. Call get_eligible_donors to find available donors.
2. Call launch_outreach_wave with the top {settings.wave_size} donor IDs (wave_number=1).
3. Call check_fulfillment_status after each wave.
4. If not fulfilled and donors remain, launch the next wave (increment wave_number).
5. Stop when fulfilled OR no more donors OR max {MAX_WAVES} waves reached.
Be decisive and minimize delays between waves."""

    model = genai.GenerativeModel(
        model_name=MODEL,
        system_instruction=system_instruction,
        tools=TOOLS,
        generation_config=genai.GenerationConfig(temperature=0.2),
    )

    await manager.broadcast({
        "event": "status_update",
        "request_id": request.id,
        "wave_number": None,
        "data": {"message": "Orchestrator started. Searching for eligible donors..."},
    })

    chat = model.start_chat()
    response = await chat.send_message_async(
        f"Blood request created (ID: {request.id}). Begin donor matching now."
    )

    # Agentic loop
    while True:
        # Check if Gemini wants to call a function
        fn_calls = [p for p in response.parts if hasattr(p, "function_call") and p.function_call.name]

        if not fn_calls:
            # No more tool calls — Gemini is done
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

        # Execute all function calls and collect results
        tool_response_parts = []
        for part in fn_calls:
            fc = part.function_call
            args = dict(fc.args)
            result_json = await ctx.execute_tool(fc.name, args)

            tool_response_parts.append(
                Part(
                    function_response=FunctionResponse(
                        name=fc.name,
                        response={"result": result_json},
                    )
                )
            )

        response = await chat.send_message_async(tool_response_parts)
