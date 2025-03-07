Using Redpanda to test FastKafka
================

<!-- WARNING: THIS FILE WAS AUTOGENERATED! DO NOT EDIT! -->

## What is FastKafka?

[FastKafka](https://fastkafka.airt.ai/) is a powerful and easy-to-use
Python library for building asynchronous services that interact with
Kafka topics. Built on top of [Pydantic](https://docs.pydantic.dev/),
[AIOKafka](https://github.com/aio-libs/aiokafka) and
[AsyncAPI](https://www.asyncapi.com/), FastKafka simplifies the process
of writing producers and consumers for Kafka topics, handling all the
parsing, networking, task scheduling and data generation automatically.
With FastKafka, you can quickly prototype and develop high-performance
Kafka-based services with minimal code, making it an ideal choice for
developers looking to streamline their workflow and accelerate their
projects.

## What is Redpanda?

Redpanda is a drop-in replacement for Kafka. Most of the Kafka tools
work out of the box with Redpanda.

From [redpanda.com](https://redpanda.com/):

> Redpanda is a Kafka®-compatible streaming data platform that is proven
> to be 10x faster and 6x lower in total costs. It is also JVM-free,
> ZooKeeper®-free, Jepsen-tested and source available.

Some of the advantages of Redpanda over Kafka are

1.  A single binary with built-in everything, no ZooKeeper® or JVM
    needed.
2.  Costs upto 6X less than Kafka.
3.  Up to 10x lower average latencies and up to 6x faster Kafka
    transactions without compromising correctness.

To learn more about Redpanda, please visit their
[website](https://redpanda.com/) or checkout this [blog
post](https://redpanda.com/blog/redpanda-vs-kafka-performance-benchmark)
comparing Redpanda and Kafka’s performance benchmarks.

## Example repo

A sample fastkafka-based library that uses Redpanda for testing, based
on this guide, can be found
[here](https://github.com/airtai/sample_fastkafka_with_redpanda).

## The process

Here are the steps we’ll be walking through to build our example:

1.  Set up the prerequisites.
2.  Clone the example repo.
3.  Explain how to write an application using FastKafka.
4.  Explain how to write a test case to test FastKafka with Redpanda.
5.  Run the test case and produce/consume messages.

## 1. Prerequisites

Before starting, make sure you have the following prerequisites set up:

1.  **Python 3.x**: A Python 3.x installation is required to run
    FastKafka. You can download the latest version of Python from the
    [official website](https://www.python.org/downloads/). You’ll also
    need to have pip installed and updated, which is Python’s package
    installer.
2.  **Docker Desktop**: Docker is used to run Redpanda, which is
    required for testing FastKafka. You can download and install Docker
    Desktop from the [official
    website](https://www.docker.com/products/docker-desktop/).
3.  **Git**: You’ll need to have Git installed to clone the example
    repo. You can download Git from the [official
    website](https://git-scm.com/downloads).

## 2. Cloning and setting up the example repo

To get started with the example code, clone the [GitHub
repository](https://github.com/airtai/sample_fastkafka_with_redpanda) by
running the following command in your terminal:

``` cmd
git clone https://github.com/airtai/sample_fastkafka_with_redpanda.git
cd sample_fastkafka_with_redpanda
```

This will create a new directory called sample_fastkafka_with_redpanda
and download all the necessary files.

### Create a virtual environment

Before writing any code, let’s [create a new virtual
environment](https://docs.python.org/3/library/venv.html#module-venv)
for our project.

A virtual environment is an isolated environment for a Python project,
which allows you to manage project-specific dependencies and avoid
conflicts between different projects.

To create a new virtual environment, run the following commands in your
terminal:

``` cmd
python3 -m venv venv
```

This will create a new directory called `venv` in your project
directory, which will contain the virtual environment.

To activate the virtual environment, run the following command:

``` cmd
source venv/bin/activate
```

This will change your shell’s prompt to indicate that you are now
working inside the virtual environment.

Finally, run the following command to upgrade `pip`, the Python package
installer:

``` cmd
pip install --upgrade pip
```

### Install Python dependencies

Next, let’s install the required Python dependencies. In this guide,
we’ll be using
[`FastKafka`](../api/fastkafka/FastKafka.md/#fastkafka.FastKafka)
to write our application code and `pytest` and `pytest-asyncio` to test
it.

You can install the dependencies from the `requirements.txt` file
provided in the cloned repository by running:

``` cmd
pip install -r requirements.txt
```

This will install all the required packages and their dependencies.

## 3. Writing server code

The `application.py` file in the cloned repository demonstrates how to
use FastKafka to consume messages from a Kafka topic, make predictions
using a predictive model, and publish the predictions to another Kafka
topic. Here is an explanation of the code:

### Preparing the demo model

First we will prepare our model using the Iris dataset so that we can
demonstrate the predictions using FastKafka. The following call
downloads the dataset and trains the model.

We will wrap the model creation into a lifespan of our app so that the
model is created just before the app is started.

``` python
from contextlib import asynccontextmanager

from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression

from fastkafka import FastKafka

ml_models = {}


@asynccontextmanager
async def lifespan(app: FastKafka):
    # Load the ML model
    X, y = load_iris(return_X_y=True)
    ml_models["iris_predictor"] = LogisticRegression(random_state=0, max_iter=500).fit(
        X, y
    )
    yield
    # Clean up the ML models and release the resources
    ml_models.clear()
```

### Messages

FastKafka uses [Pydantic](https://docs.pydantic.dev/) to parse input
JSON-encoded data into Python objects, making it easy to work with
structured data in your Kafka-based applications. Pydantic’s
[`BaseModel`](https://docs.pydantic.dev/usage/models/) class allows you
to define messages using a declarative syntax, making it easy to specify
the fields and types of your messages.

This example defines two message classes for use in a FastKafka
application:

- The `IrisInputData` class is used to represent input data for a
  predictive model. It has four fields of type
  [`NonNegativeFloat`](https://docs.pydantic.dev/usage/types/#constrained-types),
  which is a subclass of float that only allows non-negative floating
  point values.

- The `IrisPrediction` class is used to represent the output of the
  predictive model. It has a single field `species` of type string
  representing the predicted species.

These message classes will be used to parse and validate incoming data
in Kafka consumers and producers.

``` python
from pydantic import BaseModel, Field, NonNegativeFloat


class IrisInputData(BaseModel):
    sepal_length: NonNegativeFloat = Field(
        ..., example=0.5, description="Sepal length in cm"
    )
    sepal_width: NonNegativeFloat = Field(
        ..., example=0.5, description="Sepal width in cm"
    )
    petal_length: NonNegativeFloat = Field(
        ..., example=0.5, description="Petal length in cm"
    )
    petal_width: NonNegativeFloat = Field(
        ..., example=0.5, description="Petal width in cm"
    )


class IrisPrediction(BaseModel):
    species: str = Field(..., example="setosa", description="Predicted species")
```

### Application

This example shows how to initialize a FastKafka application.

It starts by defining a dictionary called `kafka_brokers`, which
contains two entries: `"localhost"` and `"production"`, specifying local
development and production Kafka brokers. Each entry specifies the URL,
port, and other details of a Kafka broker. This dictionary is used both
to generate documentation and to later run the server against one of the
given kafka broker.

Next, an instance of the
[`FastKafka`](../api/fastkafka/FastKafka.md/#fastkafka.FastKafka)
class is initialized with the minimum required arguments:

- `kafka_brokers`: a dictionary used for generating documentation

``` python
from fastkafka import FastKafka

kafka_brokers = {
    "localhost": {
        "url": "localhost",
        "description": "local development kafka broker",
        "port": 9092,
    },
    "production": {
        "url": "kafka.airt.ai",
        "description": "production kafka broker",
        "port": 9092,
        "protocol": "kafka-secure",
        "security": {"type": "plain"},
    },
}

kafka_app = FastKafka(
    title="Iris predictions",
    kafka_brokers=kafka_brokers,
    lifespan=lifespan,
)
```

### Function decorators

FastKafka provides convenient function decorators `@kafka_app.consumes`
and `@kafka_app.produces` to allow you to delegate the actual process of

- consuming and producing data to Kafka, and

- decoding and encoding JSON encode messages

from user defined functions to the framework. The FastKafka framework
delegates these jobs to AIOKafka and Pydantic libraries.

These decorators make it easy to specify the processing logic for your
Kafka consumers and producers, allowing you to focus on the core
business logic of your application without worrying about the underlying
Kafka integration.

This following example shows how to use the `@kafka_app.consumes` and
`@kafka_app.produces` decorators in a FastKafka application:

- The `@kafka_app.consumes` decorator is applied to the `on_input_data`
  function, which specifies that this function should be called whenever
  a message is received on the “input_data" Kafka topic. The
  `on_input_data` function takes a single argument which is expected to
  be an instance of the `IrisInputData` message class. Specifying the
  type of the single argument is instructing the Pydantic to use
  `IrisInputData.parse_raw()` on the consumed message before passing it
  to the user defined function `on_input_data`.

- The `@produces` decorator is applied to the `to_predictions` function,
  which specifies that this function should produce a message to the
  “predictions" Kafka topic whenever it is called. The `to_predictions`
  function takes a single integer argument `species_class` representing
  one of three possible strign values predicted by the mdoel. It creates
  a new `IrisPrediction` message using this value and then returns it.
  The framework will call the `IrisPrediction.json().encode("utf-8")`
  function on the returned value and produce it to the specified topic.

``` python
@kafka_app.consumes(topic="input_data", auto_offset_reset="latest")
async def on_input_data(msg: IrisInputData):
    species_class = ml_models["iris_predictor"].predict(
        [[msg.sepal_length, msg.sepal_width, msg.petal_length, msg.petal_width]]
    )[0]

    await to_predictions(species_class)


@kafka_app.produces(topic="predictions")
async def to_predictions(species_class: int) -> IrisPrediction:
    iris_species = ["setosa", "versicolor", "virginica"]

    prediction = IrisPrediction(species=iris_species[species_class])
    return prediction
```

## 4. Writing the test code

The service can be tested using the
[`Tester`](../api/fastkafka/testing/Tester.md/#fastkafka.testing.Tester)
instance which can be configured to start a [Redpanda
broker](../api/fastkafka/testing/LocalRedpandaBroker/) for testing
purposes. The `test.py` file in the cloned repository contains the
following code for testing.

``` python
import pytest
from application import IrisInputData, IrisPrediction, kafka_app

from fastkafka.testing import Tester

msg = IrisInputData(
    sepal_length=0.1,
    sepal_width=0.2,
    petal_length=0.3,
    petal_width=0.4,
)


@pytest.mark.asyncio
async def test():
    # Start Tester app and create local Redpanda broker for testing
    async with Tester(kafka_app).using_local_redpanda(
        tag="v23.1.2", listener_port=9092
    ) as tester:
        # Send IrisInputData message to input_data topic
        await tester.to_input_data(msg)

        # Assert that the kafka_app responded with IrisPrediction in predictions topic
        await tester.awaited_mocks.on_predictions.assert_awaited_with(
            IrisPrediction(species="setosa"), timeout=2
        )
```

The
[`Tester`](../api/fastkafka/testing/Tester.md/#fastkafka.testing.Tester)
module utilizes uses
[`LocalRedpandaBroker`](../api/fastkafka/testing/LocalRedpandaBroker.md/#fastkafka.testing.LocalRedpandaBroker)
to start and stop a Redpanda broker for testing purposes using Docker

## 5. Running the tests

We can run the tests which is in `test.py` file by executing the
following command:

``` cmd
pytest test.py
```

This will start a Redpanda broker using Docker and executes tests. The
output of the command is:

``` cmd
(venv) fastkafka@airt-ai:~/dev/sample_fastkafka_with_redpanda$ pytest
============================== test session starts ===============================
platform linux -- Python 3.10.6, pytest-7.2.2, pluggy-1.0.0
rootdir: /home/kumaran/dev/sample_fastkafka_with_redpanda, configfile: pytest.ini, testpaths: test.py
plugins: asyncio-0.21.0, anyio-3.6.2
asyncio: mode=strict
collected 1 item                                                                 

test.py .                                                                  [100%]

=============================== 1 passed in 7.28s ================================
(venv) fastkafka@airt-ai:~/dev/sample_fastkafka_with_redpanda$
```

Running the tests with the Redpanda broker ensures that your code is
working correctly with a real Kafka-like message broker, making your
tests more reliable.

### Recap

We have created an Iris classification model and encapulated it into our
[`FastKafka`](../api/fastkafka/FastKafka.md/#fastkafka.FastKafka)
application. The app will consume the `IrisInputData` from the
`input_data` topic and produce the predictions to `predictions` topic.

To test the app we have:

1.  Created the app

2.  Started our
    [`Tester`](../api/fastkafka/testing/Tester.md/#fastkafka.testing.Tester)
    class with `Redpanda` broker which mirrors the developed app topics
    for testing purposes

3.  Sent `IrisInputData` message to `input_data` topic

4.  Asserted and checked that the developed iris classification service
    has reacted to `IrisInputData` message
