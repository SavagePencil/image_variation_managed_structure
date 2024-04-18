from griptape.drivers import (
    GriptapeCloudEventListenerDriver,
    LeonardoImageGenerationDriver
)
from griptape.engines import VariationImageGenerationEngine
from griptape.events import (
    EventListener,
)
from griptape.loaders import ImageLoader
from griptape.structures import Agent
from griptape.tools import Calculator
import os
import json
import sys
from urllib.request import urlopen

# Make sure the correct number of params were sent.
# TODO: keep the extra param for now while we work through this
if (len(sys.argv) != 3):
     raise ValueError("Structure requires exactly one input parameter (JSON dictionary).")

# We're expecting a JSON dictionary. Make sure it worked.
try:
    params_dict = json.loads(sys.argv[1])
except Exception as e:
    raise ValueError(f"Structure parameter was not a valid JSON dictionary. Error: {e}")

# OK, does it have all the tasty bits
try:
    url = params_dict["url"]
except Exception as e:
    raise KeyError(f"Structure JSON dictionary missing key: {e}")

try:
    style = params_dict["style"]
except Exception as e:
    raise KeyError(f"Structure JSON dictionary missing key: {e}")

try:
    prompt = params_dict["prompt"]
except Exception as e:
    raise KeyError(f"Structure JSON dictionary missing key: {e}")

# Now make sure they're legit before actually doing anyting.

# VALIDATE THE PROMPT
if not prompt:
    raise ValueError("No string value found for prompt.")

# VALIDATE THE STYLE PARAM
# How to find Leonardo model IDs:
# 1. Go to https://app.leonardo.ai/finetuned-models
# 2. Find a model you like
# 3. Click on the model to bring up a modal
# 4. Click the "View More" button
# 5. The model ID will be listed under the model title
leonardo_model_names_to_IDs = {
    "3D Animation Style": "d69c8273-6b17-4a30-a13e-d6637ae1c644",
    "Absolute Reality v1.6": "e316348f-7773-490e-adcd-46757c738eb7",
    "Cute Characters": "50c4f43b-f086-4838-bcac-820406244cec",
    "Leonardo Signature": "291be633-cb24-434f-898f-e662799936ad",
    "Pixel Art": "e5a291b6-3990-495a-b1fa-7bd1864510a6"
}

try:
    leonardo_model_ID = leonardo_model_names_to_IDs[style]
except Exception as e:
    raise ValueError(f"Style '{style}' was not a supported style: {e}")

# VALIDATE THE URL
try:
    image_data_as_bytes = urlopen(url).read()
except Exception as e:
    raise ValueError(f"URL '{url}' was not able to be read: {e}")

# VALIDATE THE IMAGE ACTUALLY LOADS
try:
    loader = ImageLoader()
    image_artifact = loader.load(image_data_as_bytes)
except Exception as e:
    raise TypeError(f"Unable to load file at '{url}' as an image: {e}")

# Create a driver configured to use Leonardo
leonardo_driver = LeonardoImageGenerationDriver(
    api_key=os.environ.get("LEONARDO_API_KEY"),
    init_strength=0.3,
    steps=30,
    model=leonardo_model_ID,
)

driver = leonardo_driver

# Create an engine configured to use the driver.
engine = VariationImageGenerationEngine(
    image_generation_driver=driver,
)

# Let's run the engine by itself.
prompts = [
    prompt
]
negative_prompts = []
try:
    output_artifact = engine.run(prompts=prompts, negative_prompts=negative_prompts, image=image_artifact)
except:
    pass

# Send it back as a base-64 encoded string
# TODO

input = sys.argv[2]

if True:
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

