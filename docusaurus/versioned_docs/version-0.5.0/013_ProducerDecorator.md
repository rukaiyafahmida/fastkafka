
<!-- WARNING: THIS FILE WAS AUTOGENERATED! DO NOT EDIT! -->

``` python
import asyncio
from contextlib import asynccontextmanager
from unittest.mock import Mock

from pydantic import Field

from fastkafka._components.encoder.avro import avro_encoder
from fastkafka._components.encoder.json import json_encoder
from fastkafka._testing.apache_kafka_broker import ApacheKafkaBroker
from fastkafka._testing.test_utils import mock_AIOKafkaProducer_send
```

------------------------------------------------------------------------

### KafkaEvent

>      KafkaEvent (*args, **kwds)

A generic class for representing Kafka events. Based on BaseSubmodel,
bound to pydantic.BaseModel

Attributes: message (BaseSubmodel): The message contained in the Kafka
event, can be of type pydantic.BaseModel. key (bytes, optional): The
optional key used to identify the Kafka event.

``` python
event = KafkaEvent("Some message")
assert event.message == "Some message"
assert event.key == None

event = KafkaEvent("Some message", b"123")
assert event.message == "Some message"
assert event.key == b"123"
```

``` python
# # | export


# def _to_json_utf8(o: Any) -> bytes:
#     """Converts to JSON and then encodes with UTF-8"""
#     if hasattr(o, "json"):
#         return o.json().encode("utf-8")  # type: ignore
#     else:
#         return json.dumps(o).encode("utf-8")
```

``` python
# assert _to_json_utf8({"a": 1, "b": [2, 3]}) == b'{"a": 1, "b": [2, 3]}'


class A(BaseModel):
    name: str = Field()
    age: int


# assert _to_json_utf8(A(name="Davor", age=12)) == b'{"name": "Davor", "age": 12}'
```

``` python
message = A(name="Davor", age=12)
wrapped = _wrap_in_event(message)

assert type(wrapped) == KafkaEvent
assert wrapped.message == message
assert wrapped.key == None
```

``` python
message = KafkaEvent(A(name="Davor", age=12), b"123")
wrapped = _wrap_in_event(message)

assert type(wrapped) == KafkaEvent
assert wrapped.message == message.message
assert wrapped.key == b"123"
```

------------------------------------------------------------------------

<a
href="https://github.com/airtai/fastkafka/blob/main/fastkafka/_components/producer_decorator.py#L53"
target="_blank" style={{float: 'right', fontSize: 'smaller'}}>source</a>

### get_loop

>      get_loop ()

``` python
loop = get_loop()

assert isinstance(loop, asyncio.AbstractEventLoop)
```

------------------------------------------------------------------------

<a
href="https://github.com/airtai/fastkafka/blob/main/fastkafka/_components/producer_decorator.py#L65"
target="_blank" style={{float: 'right', fontSize: 'smaller'}}>source</a>

### producer_decorator

>      producer_decorator (producer_store:Dict[str,Any], func:Union[Callable[...
>                          ,Union[pydantic.main.BaseModel,fastkafka.KafkaEvent[p
>                          ydantic.main.BaseModel]]],Callable[...,Awaitable[Unio
>                          n[pydantic.main.BaseModel,fastkafka.KafkaEvent[pydant
>                          ic.main.BaseModel]]]]], topic:str,
>                          encoder_fn:Callable[[pydantic.main.BaseModel],bytes])

todo: write documentation

``` python
class MockMsg(BaseModel):
    name: str = "Micky Mouse"
    id: int = 123


mock_msg = MockMsg()

topic = "test_topic"
```

``` python
@asynccontextmanager
async def mock_producer_env(
    is_sync: bool,
) -> AsyncGenerator[
    Tuple[Mock, AIOKafkaProducer], None
]:
    try:
        with mock_AIOKafkaProducer_send() as send_mock:
            async with ApacheKafkaBroker(topics=[topic]) as bootstrap_server:
                producer = AIOKafkaProducer(bootstrap_servers=bootstrap_server)
                await producer.start()
                yield send_mock, producer
    finally:
        await producer.stop()
```

``` python
async def func(mock_msg: MockMsg) -> MockMsg:
    return mock_msg


async with mock_producer_env(is_sync=False) as (send_mock, producer):
    test_func = producer_decorator(
        {topic: (None, producer, None)}, func, topic, encoder_fn=json_encoder
    )

    assert iscoroutinefunction(test_func) == True

    value = await test_func(mock_msg)

    send_mock.assert_called_once_with(topic, mock_msg.json().encode("utf-8"), key=None)

    assert value == mock_msg
```

``` python
# Test with avro_encoder
async def func(mock_msg: MockMsg) -> MockMsg:
    return mock_msg


async with mock_producer_env(is_sync=False) as (send_mock, producer):
    test_func = producer_decorator(
        {topic: (None, producer, None)}, func, topic, encoder_fn=avro_encoder
    )

    assert iscoroutinefunction(test_func) == True

    value = await test_func(mock_msg)

    send_mock.assert_called_once_with(topic, avro_encoder(mock_msg), key=None)

    assert value == mock_msg
```

``` python
def func(mock_msg: MockMsg) -> MockMsg:
    return mock_msg


async with mock_producer_env(is_sync=True) as (send_mock, producer):
    test_func = producer_decorator(
        {topic: (None, producer, None)}, func, topic, encoder_fn=json_encoder
    )

    assert iscoroutinefunction(test_func) == False

    value = test_func(mock_msg)
    await asyncio.sleep(1)

    send_mock.assert_called_once_with(topic, mock_msg.json().encode("utf-8"), key=None)

    assert value == mock_msg
```

``` python
# Test with avro_encoder
def func(mock_msg: MockMsg) -> MockMsg:
    return mock_msg


async with mock_producer_env(is_sync=True) as (send_mock, producer):
    test_func = producer_decorator(
        {topic: (None, producer, None)}, func, topic, encoder_fn=avro_encoder
    )

    assert iscoroutinefunction(test_func) == False

    value = test_func(mock_msg)
    await asyncio.sleep(1)

    send_mock.assert_called_once_with(topic, avro_encoder(mock_msg), key=None)

    assert value == mock_msg
```

``` python
test_key = b"some_key"
```

``` python
async def func(mock_msg: MockMsg) -> KafkaEvent[MockMsg]:
    return KafkaEvent(mock_msg, key=test_key)


async with mock_producer_env(is_sync=False) as (send_mock, producer):
    test_func = producer_decorator(
        {topic: (None, producer, None)}, func, topic, encoder_fn=json_encoder
    )

    assert iscoroutinefunction(test_func) == True

    value = await test_func(mock_msg)

    send_mock.assert_called_once_with(
        topic, mock_msg.json().encode("utf-8"), key=test_key
    )

    assert value == KafkaEvent(mock_msg, key=test_key)
```

``` python
# Test with avro_encoder


async def func(mock_msg: MockMsg) -> KafkaEvent[MockMsg]:
    return KafkaEvent(mock_msg, key=test_key)


async with mock_producer_env(is_sync=False) as (send_mock, producer):
    test_func = producer_decorator(
        {topic: (None, producer, None)}, func, topic, encoder_fn=avro_encoder
    )

    assert iscoroutinefunction(test_func) == True

    value = await test_func(mock_msg)

    send_mock.assert_called_once_with(topic, avro_encoder(mock_msg), key=test_key)

    assert value == KafkaEvent(mock_msg, key=test_key)
```

``` python
async def func(mock_msg: MockMsg) -> KafkaEvent[MockMsg]:
    return KafkaEvent(mock_msg, key=test_key)


async with mock_producer_env(is_sync=False) as (send_mock, producer):
    test_func = producer_decorator(
        {topic: (None, producer, None)}, func, topic, encoder_fn=json_encoder
    )

    assert iscoroutinefunction(test_func) == True

    value = await test_func(mock_msg)

    send_mock.assert_called_once_with(
        topic, mock_msg.json().encode("utf-8"), key=test_key
    )

    assert value == KafkaEvent(mock_msg, key=test_key)
```

``` python
# Test with avro_encoder


async def func(mock_msg: MockMsg) -> KafkaEvent[MockMsg]:
    return KafkaEvent(mock_msg, key=test_key)


async with mock_producer_env(is_sync=False) as (send_mock, producer):
    test_func = producer_decorator(
        {topic: (None, producer, None)}, func, topic, encoder_fn=avro_encoder
    )

    assert iscoroutinefunction(test_func) == True

    value = await test_func(mock_msg)

    send_mock.assert_called_once_with(topic, avro_encoder(mock_msg), key=test_key)

    assert value == KafkaEvent(mock_msg, key=test_key)
```
