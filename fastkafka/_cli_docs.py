# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/024_CLI_Docs.ipynb.

# %% auto 0
__all__ = ['logger', 'docs_install_deps', 'generate_docs', 'serve_docs']

# %% ../nbs/024_CLI_Docs.ipynb 1
import asyncio
import signal
import socketserver
from http.server import SimpleHTTPRequestHandler
from types import FrameType
from typing import *

import typer

from fastkafka._components.docs_dependencies import (
    _check_npm_with_local,
    _install_docs_npm_deps,
    _install_node,
)
from ._components.helpers import _import_from_string, change_dir
from ._components.logger import get_logger

# %% ../nbs/024_CLI_Docs.ipynb 5
logger = get_logger(__name__)

# %% ../nbs/024_CLI_Docs.ipynb 8
_docs_app = typer.Typer(help="Commands for managing fastkafka app documentation")

# %% ../nbs/024_CLI_Docs.ipynb 9
@_docs_app.command(
    "install_deps",
    help="Installs dependencies for FastKafka documentation generation",
)
def docs_install_deps() -> None:
    try:
        _check_npm_with_local()
    except Exception as e:
        typer.secho(f"Unexpected internal error: {e}", err=True, fg=typer.colors.RED)
        install_confirm = typer.confirm(
            "npm not found or version is too low, do you want us to install the NodeJS and npm locally?"
        )
        if install_confirm is False:
            print("Not installing NodeJS and npm locally, exiting..")
            raise typer.Abort()
        else:
            _install_node()
    asyncio.run(_install_docs_npm_deps())


@_docs_app.command(
    "generate",
    help="Generates documentation for a FastKafka application",
)
def generate_docs(
    root_path: str = typer.Option(
        ".", help="root path under which documentation will be created"
    ),
    app: str = typer.Argument(
        ...,
        help="input in the form of 'path:app', where **path** is the path to a python file and **app** is an object of type **FastKafka**.",
    ),
) -> None:
    try:
        application = _import_from_string(app)
        application.skip_docs = False
        application.create_docs()
    except Exception as e:
        typer.secho(f"Unexpected internal error: {e}", err=True, fg=typer.colors.RED)
        raise typer.Exit(1)


@_docs_app.command(
    "serve",
    help="Generates and serves documentation for a FastKafka application",
)
def serve_docs(
    root_path: str = typer.Option(
        ".", help="root path under which documentation will be created"
    ),
    bind: str = typer.Option("127.0.0.1", help="Some info"),
    port: int = typer.Option(8000, help="Some info"),
    app: str = typer.Argument(
        ...,
        help="input in the form of 'path:app', where **path** is the path to a python file and **app** is an object of type **FastKafka**.",
    ),
) -> None:
    try:
        application = _import_from_string(app)
        application.create_docs()
        with change_dir("asyncapi/docs/"):
            server_address = (bind, port)
            handler = SimpleHTTPRequestHandler

            d = {"should_stop": False}

            def sigint_handler(
                signal: int, frame: Optional[FrameType], d: Dict[str, bool] = d
            ) -> None:
                d["should_stop"] = True

            signal.signal(signal.SIGINT, sigint_handler)
            signal.signal(signal.SIGTERM, sigint_handler)

            with socketserver.TCPServer(server_address, handler) as httpd:
                httpd.timeout = 0.1
                typer.secho(
                    f"Serving documentation on http://{server_address[0]}:{server_address[1]}"
                )
                while not d["should_stop"]:
                    httpd.handle_request()
                typer.secho(f"Interupting serving of documentation and cleaning up...")
    except Exception as e:
        typer.secho(f"Unexpected internal error: {e}", err=True, fg=typer.colors.RED)
        raise typer.Exit(1)
