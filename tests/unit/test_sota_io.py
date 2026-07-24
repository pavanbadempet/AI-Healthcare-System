"""
Unit tests for SOTA High-Performance I/O Engine (backend/sota_io.py).
"""

import os
import tempfile

import pytest

from backend.sota_io import MemoryMappedFileReader, async_stream_file_chunks


def test_mmap_reader():
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"HEALTHCARE_DICOM_HEADER_DATA_STREAM")
        tmp_path = tmp.name

    try:
        reader = MemoryMappedFileReader(tmp_path)
        data = reader.read_slice(0, 10)
        assert data == b"HEALTHCARE"
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@pytest.mark.asyncio
async def test_async_stream_chunks():
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"CHUNK_1_CHUNK_2_CHUNK_3")
        tmp_path = tmp.name

    try:
        chunks = []
        async for chunk in async_stream_file_chunks(tmp_path, chunk_size=7):
            chunks.append(chunk)

        full_content = b"".join(chunks)
        assert full_content == b"CHUNK_1_CHUNK_2_CHUNK_3"
    finally:
        import os
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
