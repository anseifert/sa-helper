from pydantic import BaseModel

from app.schemas.task import TaskOut


class AccountSummaryOut(BaseModel):
    account_key: str
    display_name: str
    task_count: int
    summary: str
    tasks: list[TaskOut]


class TaskCategoryOut(BaseModel):
    category: str
    label: str
    task_count: int
    summary: str
    tasks: list[TaskOut]


class TasksSummaryOut(BaseModel):
    priority_accounts: list[AccountSummaryOut]
    concur: TaskCategoryOut
    redhat_direct: TaskCategoryOut
    other_accounts: list[AccountSummaryOut]
