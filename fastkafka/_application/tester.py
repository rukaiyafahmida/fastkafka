# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/016_Tester.ipynb.

# %% auto 0
__all__ = ['Tester', 'mirror_producer', 'mirror_consumer']

# %% ../../nbs/016_Tester.ipynb 1
import asyncio
import inspect
from contextlib import asynccontextmanager
from typing import *

from pydantic import BaseModel

from .app import FastKafka
from .._components.meta import delegates, export, patch
from .._testing.apache_kafka_broker import ApacheKafkaBroker
from .._testing.in_memory_broker import InMemoryBroker
from .._testing.local_redpanda_broker import LocalRedpandaBroker

# %% ../../nbs/016_Tester.ipynb 6
@export("fastkafka.testing")
class Tester(FastKafka):
    __test__ = False

    @delegates(ApacheKafkaBroker.__init__)
    def __init__(
        self,
        app: Union[FastKafka, List[FastKafka]],
        *,
        broker: Optional[
            Union[ApacheKafkaBroker, LocalRedpandaBroker, InMemoryBroker]
        ] = None,
    ):
        """Mirror-like object for testing a FastFafka application

        Can be used as context manager

        """
        self.apps = app if isinstance(app, list) else [app]
        host, port = self.apps[0]._kafka_config["bootstrap_servers"].split(":")
        super().__init__(kafka_brokers={"localhost": {"url": host, "port": port}})
        self.create_mirrors()

        self.broker = broker

    @delegates(LocalRedpandaBroker.__init__)
    def using_local_redpanda(self, **kwargs: Any) -> "Tester":
        """Starts local Redpanda broker used by the Tester instance

        Args:
            listener_port: Port on which the clients (producers and consumers) can connect
            tag: Tag of Redpanda image to use to start container
            seastar_core: Core(s) to use byt Seastar (the framework Redpanda uses under the hood)
            memory: The amount of memory to make available to Redpanda
            mode: Mode to use to load configuration properties in container
            default_log_level: Log levels to use for Redpanda
            topics: List of topics to create after sucessfull redpanda broker startup
            retries: Number of retries to create redpanda service
            apply_nest_asyncio: set to True if running in notebook
            port allocation if the requested port was taken

        Returns:
            An instance of tester with Redpanda as broker
        """
        topics = set().union(*(app.get_topics() for app in self.apps))
        kwargs["topics"] = (
            topics.union(kwargs["topics"]) if "topics" in kwargs else topics
        )
        self.broker = LocalRedpandaBroker(**kwargs)

        return self

    @delegates(ApacheKafkaBroker.__init__)
    def using_local_kafka(self, **kwargs: Any) -> "Tester":
        """Starts local Kafka broker used by the Tester instance

        Args:
            data_dir: Path to the directory where the zookeepeer instance will save data
            zookeeper_port: Port for clients (Kafka brokes) to connect
            listener_port: Port on which the clients (producers and consumers) can connect
            topics: List of topics to create after sucessfull Kafka broker startup
            retries: Number of retries to create kafka and zookeeper services using random
            apply_nest_asyncio: set to True if running in notebook
            port allocation if the requested port was taken

        Returns:
            An instance of tester with Kafka as broker
        """
        topics = set().union(*(app.get_topics() for app in self.apps))
        kwargs["topics"] = (
            topics.union(kwargs["topics"]) if "topics" in kwargs else topics
        )
        self.broker = ApacheKafkaBroker(**kwargs)

        return self

    async def _start_tester(self) -> None:
        """Starts the Tester"""
        for app in self.apps:
            app.create_mocks()
            await app.__aenter__()
        self.create_mocks()
        await super().__aenter__()
        await asyncio.sleep(3)

    async def _stop_tester(self) -> None:
        """Shuts down the Tester"""
        await super().__aexit__(None, None, None)
        for app in self.apps[::-1]:
            await app.__aexit__(None, None, None)

    def create_mirrors(self) -> None:
        pass

    @asynccontextmanager
    async def _create_ctx(self) -> AsyncGenerator["Tester", None]:
        if self.broker is None:
            topics = set().union(*(app.get_topics() for app in self.apps))
            self.broker = InMemoryBroker()

        bootstrap_server = await self.broker._start()
        old_bootstrap_servers: List[str] = list()
        try:
            if isinstance(self.broker, (ApacheKafkaBroker, LocalRedpandaBroker)):
                self._set_bootstrap_servers(bootstrap_servers=bootstrap_server)
                for app in self.apps:
                    old_bootstrap_servers.append(app._kafka_config["bootstrap_servers"])
                    app._set_bootstrap_servers(bootstrap_server)
            await self._start_tester()
            try:
                yield self
            finally:
                await self._stop_tester()
        finally:
            await self.broker._stop()
            for app, server in zip(self.apps, old_bootstrap_servers):
                app._set_bootstrap_servers(server)

    async def __aenter__(self) -> "Tester":
        self._ctx = self._create_ctx()
        return await self._ctx.__aenter__()

    async def __aexit__(self, *args: Any) -> None:
        await self._ctx.__aexit__(*args)

# %% ../../nbs/016_Tester.ipynb 11
def mirror_producer(topic: str, producer_f: Callable[..., Any]) -> Callable[..., Any]:
    msg_type = inspect.signature(producer_f).return_annotation

    async def skeleton_func(msg: BaseModel) -> None:
        pass

    mirror_func = skeleton_func
    sig = inspect.signature(skeleton_func)

    # adjust name
    mirror_func.__name__ = "on_" + topic

    # adjust arg and return val
    sig = sig.replace(
        parameters=[
            inspect.Parameter(
                name="msg",
                annotation=msg_type,
                kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
            )
        ]
    )

    mirror_func.__signature__ = sig  # type: ignore

    return mirror_func

# %% ../../nbs/016_Tester.ipynb 13
def mirror_consumer(topic: str, consumer_f: Callable[..., Any]) -> Callable[..., Any]:
    msg_type = inspect.signature(consumer_f).parameters["msg"]

    async def skeleton_func(msg: BaseModel) -> BaseModel:
        return msg

    mirror_func = skeleton_func
    sig = inspect.signature(skeleton_func)

    # adjust name
    mirror_func.__name__ = "to_" + topic

    # adjust arg and return val
    sig = sig.replace(parameters=[msg_type], return_annotation=msg_type.annotation)

    mirror_func.__signature__ = sig  # type: ignore
    return mirror_func

# %% ../../nbs/016_Tester.ipynb 15
@patch
def create_mirrors(self: Tester) -> None:
    for app in self.apps:
        for topic, (consumer_f, _, _) in app._consumers_store.items():
            mirror_f = mirror_consumer(topic, consumer_f)
            mirror_f = self.produces()(mirror_f)  # type: ignore
            setattr(self, mirror_f.__name__, mirror_f)
        for topic, (producer_f, _, _) in app._producers_store.items():
            mirror_f = mirror_producer(topic, producer_f)
            mirror_f = self.consumes()(mirror_f)  # type: ignore
            setattr(self, mirror_f.__name__, mirror_f)
