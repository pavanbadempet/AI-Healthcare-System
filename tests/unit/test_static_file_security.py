from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.responses import FileResponse

from backend import main


@pytest.mark.asyncio
async def test_spa_catchall_rejects_decoded_path_traversal():
    with pytest.raises(HTTPException) as exc_info:
        await main.serve_frontend("../../backend/auth.py", request=None)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_spa_catchall_serves_file_inside_frontend_dist():
    response = await main.serve_frontend("index.html", request=None)

    assert isinstance(response, FileResponse)
    assert Path(response.path).resolve() == Path(main._frontend_dist, "index.html").resolve()
