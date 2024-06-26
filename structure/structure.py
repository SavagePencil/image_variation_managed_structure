from dotenv import load_dotenv
from griptape.artifacts import TextArtifact
from griptape.drivers import (
    GriptapeCloudEventListenerDriver,
    LeonardoImageGenerationDriver,
)
from griptape.engines import VariationImageGenerationEngine
from griptape.events import FinishStructureRunEvent
from griptape.loaders import ImageLoader
import os
import json
import sys
from urllib.request import urlopen


def is_running_in_managed_environment() -> bool:
    """Determine if the program is running in a managed environment (e.g., Griptape Cloud or Skatepark emulator).
    Returns:
        bool: True if the program is running in a managed environment, False otherwise.
    """
    return "GT_CLOUD_RUN_ID" in os.environ


def get_listener_api_key() -> str:
    """The event driver expects a Griptape API Key as a parameter.
    When your program is running in Griptape Cloud, you will need to provide a 
    valid Griptape API Key in the GT_CLOUD_API_KEY environment variable 
    in order to authorize calls. 
    You can create an API Key by visiting https://cloud.griptape.ai/keys 
    When running in Skatepark, the API key is not needed since it isn't validating calls.

    Returns:
        The Griptape API Key to authorize calls.
    """
    api_key = os.environ.get("GT_CLOUD_API_KEY")
    if is_running_in_managed_environment() and not api_key:
        print("""
              ****WARNING****: No value was found for the 'GT_CLOUD_API_KEY' environment variable.
              This environment variable is required when running in Griptape Cloud for authorization.
              You can generate a Griptape API Key by visiting https://cloud.griptape.ai/keys.
              Specify it as an environment variable when creating a Managed Structure in Griptape Cloud.
              """
              )
    return api_key


# If we're doing local development (not even within the emulator), we need some env vars.
if not is_running_in_managed_environment():
    load_dotenv()

# Make sure the correct number of params were sent.
if len(sys.argv) != 2:
    raise ValueError("Program requires exactly one input parameter (JSON dictionary).")

# We're expecting a JSON dictionary. Make sure it worked.
try:
    params_dict = json.loads(sys.argv[1])
except Exception as e:
    raise ValueError(f"Program parameter was not a valid JSON dictionary. Error: {e}")

# OK, does it have all the tasty bits
try:
    url = params_dict["url"]
except Exception as e:
    raise KeyError(f"Program JSON dictionary missing key: {e}")

try:
    style = params_dict["style"]
except Exception as e:
    raise KeyError(f"Program JSON dictionary missing key: {e}")

try:
    prompt = params_dict["prompt"]
except Exception as e:
    raise KeyError(f"Program JSON dictionary missing key: {e}")

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
    "Pixel Art": "e5a291b6-3990-495a-b1fa-7bd1864510a6",
}

try:
    leonardo_model_ID = leonardo_model_names_to_IDs[style]
except Exception as e:
    raise ValueError(f"Style '{style}' was not a supported style: {e}")

# VALIDATE OUR KEY
leonardo_api_key = os.environ.get("LEONARDO_API_KEY")
if not leonardo_api_key:
    raise ValueError(f"No value found for `LEONARDO_API_KEY`.")

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
    api_key=leonardo_api_key,
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
prompts = [prompt]
negative_prompts = []
try:
    output_artifact = engine.run(
        prompts=prompts, negative_prompts=negative_prompts, image=image_artifact
    )
except:
    pass

# We will send the newly-generated image back as a base-64 encoded string
if is_running_in_managed_environment():
    # Let everyone know we're done

    # We need an event driver to communicate events from our program back to Skatepark
    event_driver = GriptapeCloudEventListenerDriver(
        api_key=get_listener_api_key()
    )

    # If we were running as a Griptape Structure (e.g., Agent, Pipeline, Workflow, etc.),
    # it would already be equipped to send the completed event.
    # Since we're not using those, we have to manually publish the FinishStructureRunEvent.
    task_input = TextArtifact(value=sys.argv[1])
    done_event = FinishStructureRunEvent(
        output_task_input=task_input, output_task_output=output_artifact
    )

    event_driver.publish_event(done_event)
