# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/097_Docs_Dependencies.ipynb.

# %% auto 0
__all__ = ['logger', 'npm_required_major_version', 'node_version', 'node_fname', 'node_url', 'local_path', 'tgz_path',
           'node_path']

# %% ../../nbs/097_Docs_Dependencies.ipynb 2
import asyncio
import os
import shutil
import subprocess  # nosec Issue: [B404:blacklist]
import sys
import tarfile
from pathlib import Path
from tempfile import TemporaryDirectory

from .helpers import in_notebook
from .logger import get_logger

if in_notebook():
    from tqdm.notebook import tqdm
else:
    from tqdm import tqdm

# %% ../../nbs/097_Docs_Dependencies.ipynb 4
logger = get_logger(__name__)

# %% ../../nbs/097_Docs_Dependencies.ipynb 5
npm_required_major_version = 9


def _check_npm(required_major_version: int = npm_required_major_version) -> None:
    if shutil.which("npm") is not None:
        cmd = "npm --version"
        proc = subprocess.run(  # nosec [B602:subprocess_popen_with_shell_equals_true]
            cmd,
            shell=True,
            check=True,
            capture_output=True,
        )
        major_version = int(proc.stdout.decode("UTF-8").split(".")[0])
        if major_version < required_major_version:
            raise RuntimeError(
                f"Found installed npm major version: {major_version}, required npx major version: {required_major_version}. To use documentation features of FastKafka, please update npm"
            )
    else:
        raise RuntimeError(
            f"npm not found, to use documentation generation features of FastKafka, you must have npm >= {required_major_version} installed"
        )

# %% ../../nbs/097_Docs_Dependencies.ipynb 10
node_version = "v18.15.0"
node_fname = f"node-{node_version}-linux-x64"
node_url = f"https://nodejs.org/dist/{node_version}/{node_fname}.tar.xz"
local_path = Path(os.environ["HOME"]) / ".local"
tgz_path = local_path / f"{node_fname}.tar.xz"
node_path = local_path / f"{node_fname}"


def _check_npm_with_local(node_path: Path = node_path) -> None:
    try:
        _check_npm()
    except RuntimeError as e:
        if (node_path / "bin").exists():
            logger.info("Found local installation of NodeJS.")
            os.environ["PATH"] = os.environ["PATH"] + f":{node_path}/bin"
            _check_npm()
        else:
            raise e

# %% ../../nbs/097_Docs_Dependencies.ipynb 13
def _install_node(
    *,
    node_url: str = node_url,
    local_path: Path = local_path,
    tgz_path: Path = tgz_path,
) -> None:
    try:
        import requests
    except Exception as e:
        msg = "Please install docs version of fastkafka using 'pip install fastkafka[docs]' command"
        logger.error(msg)
        raise RuntimeError(msg)

    logger.info("Installing NodeJS...")
    local_path.mkdir(exist_ok=True, parents=True)
    response = requests.get(
        node_url,
        stream=True,
    )
    try:
        total = response.raw.length_remaining // 128
    except Exception:
        total = None

    with open(tgz_path, "wb") as f:
        for data in tqdm(response.iter_content(chunk_size=128), total=total):
            f.write(data)

    with tarfile.open(tgz_path) as tar:
        for tarinfo in tar:
            tar.extract(tarinfo, local_path)

    os.environ["PATH"] = os.environ["PATH"] + f":{node_path}/bin"
    logger.info(f"Node installed in {node_path}.")

# %% ../../nbs/097_Docs_Dependencies.ipynb 16
async def _install_docs_npm_deps() -> None:
    with TemporaryDirectory() as d:
        cmd = (
            "npx -y -p @asyncapi/generator ag https://raw.githubusercontent.com/asyncapi/asyncapi/master/examples/simple.yml @asyncapi/html-template -o "
            + d
        )

        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode == 0:
            logger.info("AsyncAPI generator installed")
        else:
            logger.error("AsyncAPI generator NOT installed!")
            logger.info(
                f"stdout of '$ {cmd}'{stdout.decode('UTF-8')} \n return_code={proc.returncode}"
            )
            logger.info(
                f"stderr of '$ {cmd}'{stderr.decode('UTF-8')} \n return_code={proc.returncode}"
            )
            raise ValueError(
                f"""AsyncAPI generator NOT installed, used '$ {cmd}'
----------------------------------------
stdout:
{stdout.decode("UTF-8")}
----------------------------------------
stderr:
{stderr.decode("UTF-8")}
----------------------------------------
return_code={proc.returncode}"""
            )
