from fastapi import APIRouter

from doppelbank.veneer.common import VeneerRequest, VeneerResponse

router = APIRouter()


class HeartbeatRequest(VeneerRequest):
    pass


class HeartbeatResponse(VeneerResponse):
    ok: bool


@router.post("/link/heartbeat")
async def link_heartbeat(_request: HeartbeatRequest | None = None) -> HeartbeatResponse:
    return HeartbeatResponse(ok=True)
