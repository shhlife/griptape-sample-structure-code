import os
from typing import List

import typer
from griptape.artifacts import ListArtifact, TextArtifact
from griptape.drivers import GriptapeCloudEventListenerDriver
from griptape.events import (
    EventBus,
    EventListener,
    FinishStructureRunEvent,
    StartActionsSubtaskEvent,
)
from griptape.structures import Agent


def setup_cloud_listener():
    # Are we running in a managed environment?
    if "GT_CLOUD_STRUCTURE_RUN_ID" in os.environ:
        # If so, the runtime takes care of loading the .env file
        EventBus.add_event_listener(
            EventListener(
                event_listener_driver=GriptapeCloudEventListenerDriver(),
            )
        )
    else:
        EventBus.add_event_listener(
            EventListener(
                event_types=[StartActionsSubtaskEvent],
            )
        )
        # If not, we need to load the .env file ourselves
        from dotenv import load_dotenv

        load_dotenv()


app = typer.Typer(add_completion=False)


@app.command()
def run(args: List[str] = typer.Argument(...)):
    """Run the agent with inputs."""

    # If you want to run a Griptape Structure, set this to True
    # otherwise, if you're just running regular Python code, set it to False
    use_structure = True

    if use_structure:
        # Setup the cloud listener before Griptape Structure
        setup_cloud_listener()

        # Run the Griptape Structure
        agent = Agent()
        agent.run(args)
    else:
        # Run whatever code you want and make sure to save the output(s) as a TextArtifact(s)
        agent = Agent()
        agent.run(args)
        # output_artifact_prompt = TextArtifact(agent.output)

        # Create Input and Output Artifacts
        task_input = TextArtifact(value=None)
        task_output = ListArtifact([agent.output])
        print(task_output)

        # Setup the cloud listener after your code, and before
        # publishing the FinishStructureRunEvent
        setup_cloud_listener()

        # Create the FinishStructureRunEvent
        done_event = FinishStructureRunEvent(
            output_task_input=task_input, output_task_output=task_output
        )

        # Publish the FinishStructureRunEvent
        EventBus.publish_event(done_event, flush=True)


if __name__ == "__main__":
    app()
