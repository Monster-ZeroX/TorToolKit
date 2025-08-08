from typing import Union, Optional, List, Tuple
import asyncio
import logging
import os
import shlex
import time

# ref https://info.nrao.edu/computing/guide/file-access-and-archiving/7zip/7z-7za-command-line-guide
torlog = logging.getLogger(__name__)

DEFAULT_SPLIT_SIZE_MB = 1900


async def cli_call(cmd: Union[str, List[str]]) -> Tuple[str, str, int]:
    torlog.info("Got cmd:- %s", cmd)
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)
    elif isinstance(cmd, (list, tuple)):
        pass
    else:
        return None, None, -1

    torlog.info("Exc cmd:- %s", cmd)

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stderr=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

    stdout = stdout.decode().strip()
    stderr = stderr.decode().strip()

    return stdout, stderr, process.returncode

async def split_in_zip(
    path: str,
    size: Optional[int] = None,
    compression_level: int = 0,
    output_dir: Optional[str] = None,
):
    """Split a file into multiple zip archives.

    Args:
        path: Path to the file to be archived.
        size: Maximum part size in bytes. Defaults to ``DEFAULT_SPLIT_SIZE_MB`` MB.
        compression_level: 7z compression level (0-9).
        output_dir: Optional directory for the resulting archives.

    Returns:
        Path to the directory containing the split archives or ``None`` on error.
    """
    if os.path.exists(path) and os.path.isfile(path):
        fname = os.path.basename(path)
        if output_dir:
            bdir = os.path.abspath(output_dir)
        else:
            bdir = os.path.join(os.path.dirname(path), str(time.time()).replace(".", ""))
        os.makedirs(bdir, exist_ok=True)

        if size is None:
            size_mb = DEFAULT_SPLIT_SIZE_MB
        else:
            size_mb = int(int(size) / (1024 * 1024)) - 10
        cmd = (
            f'7z a -tzip -mx={compression_level} "{bdir}/{fname}.zip" '
            f'"{path}" -v{size_mb}m'
        )

        _, err, _ = await cli_call(cmd)

        if err:
            torlog.error("Error in zip split %s", err)
            return None
        return bdir
    return None


async def add_to_zip(
    path: str,
    size: Optional[int] = None,
    split: bool = True,
    compression_level: int = 0,
    output_dir: Optional[str] = None,
):
    """Archive a path into a zip optionally splitting it.

    Args:
        path: File or directory to archive.
        size: Maximum part size in bytes when ``split`` is ``True``.
        split: Whether to split the archive in parts.
        compression_level: 7z compression level (0-9).
        output_dir: Optional directory for the resulting archives.

    Returns:
        Path to the directory containing the archive or ``None`` on error.
    """
    if os.path.exists(path):
        fname = os.path.basename(path)
        if output_dir:
            base_dir = os.path.abspath(output_dir)
        else:
            base_dir = os.path.join(os.path.dirname(path), str(time.time()).replace(".", ""))
        os.makedirs(base_dir, exist_ok=True)

        bdir = os.path.join(base_dir, fname)
        os.makedirs(bdir, exist_ok=True)

        if size is None:
            size_mb = DEFAULT_SPLIT_SIZE_MB
        else:
            size_mb = int(int(size) / (1024 * 1024)) - 10

        total_size = get_size(path)
        if total_size > size_mb and split:
            cmd = (
                f'7z a -tzip -mx={compression_level} "{bdir}/{fname}.zip" '
                f'"{path}" -v{size_mb}m'
            )
        else:
            cmd = f'7z a -tzip -mx={compression_level} "{bdir}/{fname}.zip" "{path}"'

        _, err, _ = await cli_call(cmd)

        if err:
            torlog.error("Error in zip split %s", err)
            return None
        return bdir
    return None

def get_size(start_path = '.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)

    return total_size/(1024*1024)

async def extract_archive(path, password=""):
    if os.path.exists(path):
        if os.path.isfile(path):
            if str(path).endswith((".zip", "7z", "tar", "gzip2", "iso", "wim", "rar", "tar.gz","tar.bz2")):
                # check userdata
                userpath = os.path.join(os.getcwd(), "userdata")
                if not os.path.exists(userpath):
                    os.mkdir(userpath)
                
                extpath = os.path.join(userpath, str(time.time()).replace(".",""))
                os.mkdir(extpath)
                
                extpath = os.path.join(extpath,os.path.basename(path))
                if not os.path.exists(extpath):
                    os.mkdir(extpath)

                if str(path).endswith(("tar","tar.gz","tar.bz2")):
                    cmd = f'tar -xvf "{path}" -C "{extpath}" --warning=none'
                else:
                    cmd = f'7z e -y "{path}" "-o{extpath}" "-p{password}"'
                
                out, err, rcode = await cli_call(cmd)
                
                if err:
                    if "Wrong password" in err:
                        return "Wrong Password"
                    else:
                        torlog.error(err)
                        torlog.error(out)
                        return False
                else:
                    return extpath
        else:
            # False means that the stuff can be upload but cant be extracted as its a dir
            return False
    else:
        # None means fetal error and cant be ignored
        return None 

#7z e -y {path} {ext_path}
#/setpassword jobid password
