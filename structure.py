import sys

from griptape.drivers import (
    GriptapeCloudEventListenerDriver,
)
from griptape.events import (
    EventListener,
)
from griptape.structures import Agent
from griptape.tools import Calculator

input = sys.argv[1]

structure = Agent(
    tools=[Calculator(off_prompt=False)],
    event_listeners=[
        EventListener(
            driver=GriptapeCloudEventListenerDriver(
                base_url="http://127.0.0.1:5000", api_key="..."
            ),
        )
    ],
)

structure.run(input)
