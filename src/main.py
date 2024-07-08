"""Main script file."""

import asyncio
import hashlib
import logging
import tempfile
from pathlib import Path
from zipfile import ZipFile

from aiohttp import ClientSession

REPO_URL: str = (
    'https://gitea.radium.group/radium/' +
    'project-configuration/archive/master.zip'
)
CHUNK_SIZE: int = 1024
HASH_BLOCK_SIZE: int = 4096

logging.basicConfig(level=logging.INFO)


async def download_and_extract_zip(
    session: ClientSession, url: str, zip_path: Path, extract_path: Path,
) -> None:
    """Download and extract zip file.

    Args:
        session (ClientSession): aiohttp client session.
        url (str): URL to download.
        zip_path (Path): Path to save the zip file.
        extract_path (Path): Path to extract files.
    """
    async with session.get(url) as response:
        response.raise_for_status()
        with zip_path.open('wb') as zip_file:
            async for chunk in response.content.iter_chunked(CHUNK_SIZE):
                zip_file.write(chunk)

    with ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)


async def compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of a file.

    Args:
        file_path (Path): Path to the file.

    Returns:
        str: SHA256 hash of the file.
    """
    sha256_hash = hashlib.sha256()
    with file_path.open('rb') as file_obj:
        block = file_obj.read(HASH_BLOCK_SIZE)
        while block:
            sha256_hash.update(block)
            block = file_obj.read(HASH_BLOCK_SIZE)
    return sha256_hash.hexdigest()


async def process_files(
    zip_path: Path,
    dir_path: Path,
    session: ClientSession,
) -> None:
    """Process files in the directory.

    Args:
        zip_path (Path): Path to the zip file.
        dir_path (Path): Path to the directory.
        session (ClientSession): aiohttp client session.
    """
    await download_and_extract_zip(session, REPO_URL, zip_path, dir_path)

    for file_path in dir_path.glob('**/*'):
        if file_path.is_file():
            file_hash = await compute_file_hash(file_path)
            log_message(file_path, file_hash)


def log_message(file_path: Path, file_hash: str) -> None:
    """Log the file path and its hash.

    Args:
        file_path (Path): Path to the file.
        file_hash (str): Computed hash of the file.
    """
    message = '{0}: {1}'.format(file_path, file_hash)
    logging.info(message)


async def main() -> None:
    """Entry point for the script."""
    async with ClientSession() as session:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            zip_path = temp_dir_path / 'project-configuration.zip'
            await process_files(zip_path, temp_dir_path, session)


if __name__ == '__main__':
    asyncio.run(main())
