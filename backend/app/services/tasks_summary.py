from collections import Counter

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.task import TaskOut
from app.schemas.tasks_summary import AccountSummaryOut, TaskCategoryOut, TasksSummaryOut
from app.services.tasks_query import list_open_tasks
from app.utils.priority_accounts import PRIORITY_ACCOUNTS, match_priority_account

_TYPE_LABELS = {
    "user_owes_reply": "replies owed",
    "customer_ask_pending": "customer waiting",
    "schedule_meeting": "meetings",
    "send_docs": "documents to send",
    "send_data": "data to send",
    "stale_thread": "stale threads",
    "concur_payment": "Concur items",
    "concur_overdue": "Concur overdue",
    "redhat_attention": "Red Hat actions",
    "drive_mention": "Drive mentions",
    "calendar_action": "calendar items",
}


def _summarize_task_types(tasks: list[TaskOut]) -> str:
    if not tasks:
        return "No open items"
    counts = Counter(t.task_type for t in tasks)
    parts: list[str] = []
    for task_type, count in counts.most_common():
        label = _TYPE_LABELS.get(task_type, task_type.replace("_", " "))
        parts.append(f"{count} {label}")
    return "; ".join(parts[:5])


def _account_key_for_task(task: TaskOut) -> str | None:
    return match_priority_account(
        company_name=task.company_name,
        title=task.title,
        description=task.description,
    )


async def build_tasks_summary(session: AsyncSession) -> TasksSummaryOut:
    tasks = await list_open_tasks(session)

    concur_tasks = [t for t in tasks if t.task_type in ("concur_payment", "concur_overdue")]
    redhat_tasks = [t for t in tasks if t.task_type == "redhat_attention"]
    account_buckets: dict[str, list[TaskOut]] = {a.key: [] for a in PRIORITY_ACCOUNTS}
    other_buckets: dict[str, list[TaskOut]] = {}

    for task in tasks:
        if task.task_type in ("concur_payment", "concur_overdue", "redhat_attention"):
            continue
        key = _account_key_for_task(task)
        if key:
            account_buckets[key].append(task)
        else:
            name = task.company_name or "Unassigned"
            other_buckets.setdefault(name, []).append(task)

    priority_accounts = [
        AccountSummaryOut(
            account_key=account.key,
            display_name=account.display_name,
            task_count=len(account_buckets[account.key]),
            summary=_summarize_task_types(account_buckets[account.key]),
            tasks=sorted(
                account_buckets[account.key],
                key=lambda t: t.created_at,
            ),
        )
        for account in PRIORITY_ACCOUNTS
    ]

    other_accounts = [
        AccountSummaryOut(
            account_key=name.lower().replace(" ", "_"),
            display_name=name,
            task_count=len(bucket),
            summary=_summarize_task_types(bucket),
            tasks=sorted(bucket, key=lambda t: t.created_at),
        )
        for name, bucket in sorted(other_buckets.items(), key=lambda x: x[0].lower())
    ]

    overdue = sum(1 for t in concur_tasks if t.task_type == "concur_overdue")
    concur_summary = _summarize_task_types(concur_tasks)
    if overdue:
        concur_summary = f"{overdue} overdue; {concur_summary}"

    return TasksSummaryOut(
        priority_accounts=priority_accounts,
        concur=TaskCategoryOut(
            category="concur",
            label="Concur / payment requests",
            task_count=len(concur_tasks),
            summary=concur_summary,
            tasks=sorted(concur_tasks, key=lambda t: t.created_at),
        ),
        redhat_direct=TaskCategoryOut(
            category="redhat_direct",
            label="Red Hat — needs your attention",
            task_count=len(redhat_tasks),
            summary=_summarize_task_types(redhat_tasks),
            tasks=sorted(redhat_tasks, key=lambda t: t.created_at),
        ),
        other_accounts=other_accounts,
    )
