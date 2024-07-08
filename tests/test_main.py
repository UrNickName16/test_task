"""Tests for the main module."""

import hashlib
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import ClientSession, ClientResponseError
from aioresponses import aioresponses

from src.main import REPO_URL, compute_file_hash, main, process_files

ZIP_FILE_NAME = 'project-configuration.zip'
HTTP_STATUS_SERVER_ERROR = 500


@pytest.mark.asyncio()
async def test_process_files():
    """Test the process_files function."""
    with aioresponses() as mock_response:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_zip_file:
            with zipfile.ZipFile(tmp_zip_file.name, 'w') as zipf:
                zipf.writestr('test.txt', 'Test content')
            tmp_zip_file.seek(0)
            mock_response.get(REPO_URL, body=tmp_zip_file.read())

        async with ClientSession() as session:
            await run_process_files(session)


async def run_process_files(session: ClientSession):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        zip_path = temp_dir_path / ZIP_FILE_NAME
        test_file_path = temp_dir_path / 'test.txt'

        await process_files(zip_path, temp_dir_path, session)

        assert zip_path.exists()
        assert test_file_path.exists()
        assert test_file_path.read_text() == 'Test content'


@pytest.mark.asyncio()
async def test_compute_sha256():
    """Test the compute_sha256 function."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        test_file_path = temp_dir_path / 'test_file.txt'
        test_file_path.write_text('test content')

        sha256_hash = hashlib.sha256()
        sha256_hash.update('test content'.encode())

        result_hash = await compute_file_hash(test_file_path)
        assert result_hash == sha256_hash.hexdigest()


async def mock_get():
    mock_resp = MagicMock()
    mock_resp.__aenter__.return_value = mock_resp
    mock_resp.__aexit__.return_value = False
    mock_resp.get = AsyncMock()
    return mock_resp


@pytest.mark.asyncio()
async def test_main(mocker):
    """Test the main function."""
    mocker.patch('src.main.process_files', return_value=None)

    mocker.patch('aiohttp.ClientSession', new=mock_get)

    await main()


@pytest.mark.asyncio()
async def test_network_failure():
    """Test network failure handling."""
    with aioresponses() as mock_response:
        mock_response.get(REPO_URL, status=HTTP_STATUS_SERVER_ERROR)
        async with ClientSession() as session:
            await run_network_failure(session)


async def run_network_failure(session: ClientSession):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        zip_path = temp_dir_path / ZIP_FILE_NAME

        with pytest.raises(ClientResponseError):
            await process_files(zip_path, temp_dir_path, session)
