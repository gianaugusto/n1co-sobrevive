from dataclasses import dataclass
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status

from forgetme.api.auth import READ_PERMISSION, WRITE_PERMISSION, require_permission
from forgetme.api.schemas import CreateProcessIn, ProcessOut, SubscriberOut
from forgetme.application.use_cases import (
    CreateProcess,
    GetProcess,
    ListProcesses,
    ListSubscribers,
    RetrySubscriber,
)


@dataclass(frozen=True)
class UseCases:
    create_process: CreateProcess
    get_process: GetProcess
    list_processes: ListProcesses
    list_subscribers: ListSubscribers
    retry_subscriber: RetrySubscriber


def get_use_cases(request: Request) -> UseCases:
    return request.app.state.use_cases  # type: ignore[no-any-return]


router = APIRouter()
read = Depends(require_permission(READ_PERMISSION))
write = Depends(require_permission(WRITE_PERMISSION))


@router.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post(
    "/api/v1/processes",
    response_model=ProcessOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[write],
    tags=["processes"],
)
async def create_process(
    body: CreateProcessIn, use_cases: UseCases = Depends(get_use_cases)
) -> ProcessOut:
    process = await use_cases.create_process.execute(body.tenant_id, body.key, body.type)
    return ProcessOut.from_domain(process)


@router.get(
    "/api/v1/processes",
    response_model=list[ProcessOut],
    dependencies=[read],
    tags=["processes"],
)
async def list_processes(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    use_cases: UseCases = Depends(get_use_cases),
) -> list[ProcessOut]:
    processes = await use_cases.list_processes.execute(limit, offset)
    return [ProcessOut.from_domain(p) for p in processes]


@router.get(
    "/api/v1/processes/{process_id}",
    response_model=ProcessOut,
    dependencies=[read],
    tags=["processes"],
)
async def get_process(process_id: UUID, use_cases: UseCases = Depends(get_use_cases)) -> ProcessOut:
    return ProcessOut.from_domain(await use_cases.get_process.execute(process_id))


@router.post(
    "/api/v1/processes/{process_id}/subscribers/{name}/retry",
    response_model=ProcessOut,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[write],
    tags=["processes"],
)
async def retry_subscriber(
    process_id: UUID, name: str, use_cases: UseCases = Depends(get_use_cases)
) -> ProcessOut:
    process = await use_cases.retry_subscriber.execute(process_id, name)
    return ProcessOut.from_domain(process)


@router.get(
    "/api/v1/subscribers",
    response_model=list[SubscriberOut],
    dependencies=[read],
    tags=["subscribers"],
)
async def list_subscribers(use_cases: UseCases = Depends(get_use_cases)) -> list[SubscriberOut]:
    return [SubscriberOut.from_domain(s) for s in await use_cases.list_subscribers.execute()]
