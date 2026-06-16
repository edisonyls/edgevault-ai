from uuid import UUID

from asyncpg import Pool, Record
from asyncpg.exceptions import UniqueViolationError

from app.schemas.uploads import UploadStatus

UPLOAD_RETURNING_COLUMNS = """
    id,
    text,
    original_filename,
    display_filename,
    stored_filename,
    file_path,
    mime_type,
    file_size,
    status,
    created_at,
    updated_at
"""

DISPLAY_FILENAME_UNIQUE_CONSTRAINTS = {
    "idx_resume_uploads_display_filename",
    "idx_resume_uploads_workspace_display_filename",
}


class UniqueDisplayFilenameError(Exception):
    pass


class UploadRepository:
    def __init__(self, database_pool: Pool, workspace_id: UUID) -> None:
        self.database_pool = database_pool
        self.workspace_id = workspace_id

    async def create(
        self,
        *,
        original_filename: str,
        display_filename: str,
        stored_filename: str,
        file_path: str | None,
        mime_type: str,
        file_size: int,
    ) -> Record:
        try:
            async with self.database_pool.acquire() as connection:
                return await connection.fetchrow(
                    f"""
                    INSERT INTO resume_uploads (
                        workspace_id,
                        original_filename,
                        display_filename,
                        stored_filename,
                        file_path,
                        mime_type,
                        file_size
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING
                        {UPLOAD_RETURNING_COLUMNS}
                    """,
                    self.workspace_id,
                    original_filename,
                    display_filename,
                    stored_filename,
                    file_path,
                    mime_type,
                    file_size,
                )
        except UniqueViolationError as exc:
            if exc.constraint_name not in DISPLAY_FILENAME_UNIQUE_CONSTRAINTS:
                raise

            raise UniqueDisplayFilenameError from exc

    async def list(
        self,
        *,
        status_filter: UploadStatus | None,
        limit: int,
        offset: int,
    ) -> list[Record]:
        values: list[object] = []
        where = ["workspace_id = $1"]
        values.append(self.workspace_id)

        if status_filter is not None:
            values.append(status_filter)
            where.append(f"status = ${len(values)}::resume_upload_status")

        values.extend([limit, offset])
        limit_placeholder = f"${len(values) - 1}"
        offset_placeholder = f"${len(values)}"

        async with self.database_pool.acquire() as connection:
            return await connection.fetch(
                f"""
                SELECT
                    {UPLOAD_RETURNING_COLUMNS}
                FROM resume_uploads
                WHERE {" AND ".join(where)}
                ORDER BY created_at DESC, id DESC
                LIMIT {limit_placeholder}
                OFFSET {offset_placeholder}
                """,
                *values,
            )

    async def get(self, upload_id: UUID) -> Record | None:
        async with self.database_pool.acquire() as connection:
            return await connection.fetchrow(
                f"""
                SELECT
                    {UPLOAD_RETURNING_COLUMNS}
                FROM resume_uploads
                WHERE id = $1
                  AND workspace_id = $2
                """,
                upload_id,
                self.workspace_id,
            )

    async def update(
        self,
        upload_id: UUID,
        update_data: dict[str, object],
    ) -> Record | None:
        set_clauses = []
        values: list[object] = []

        for column, value in update_data.items():
            values.append(value)
            placeholder = f"${len(values)}"
            if column == "status":
                placeholder = f"{placeholder}::resume_upload_status"
            set_clauses.append(f"{column} = {placeholder}")

        values.extend([upload_id, self.workspace_id])

        try:
            async with self.database_pool.acquire() as connection:
                return await connection.fetchrow(
                    f"""
                    UPDATE resume_uploads
                    SET {", ".join(set_clauses)}
                    WHERE id = ${len(values) - 1}
                      AND workspace_id = ${len(values)}
                    RETURNING
                        {UPLOAD_RETURNING_COLUMNS}
                    """,
                    *values,
                )
        except UniqueViolationError as exc:
            if exc.constraint_name not in DISPLAY_FILENAME_UNIQUE_CONSTRAINTS:
                raise

            raise UniqueDisplayFilenameError from exc

    async def delete(self, upload_id: UUID) -> bool:
        async with self.database_pool.acquire() as connection:
            result = await connection.execute(
                """
                DELETE FROM resume_uploads
                WHERE id = $1
                  AND workspace_id = $2
                """,
                upload_id,
                self.workspace_id,
            )

        return result != "DELETE 0"
