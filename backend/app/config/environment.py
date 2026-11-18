"""Environment loading with an explicit, isolated evaluation mode."""

import os
from pathlib import Path

from dotenv import dotenv_values, load_dotenv


def load_application_environment():
    """Load exactly one configuration source family before application imports."""
    evaluation_file = os.getenv("EVALUATION_ENV_FILE")
    if evaluation_file:
        path = Path(evaluation_file).resolve()
        if not path.is_file():
            raise RuntimeError("EVALUATION_ENV_FILE does not exist")
        for key, value in dotenv_values(path).items():
            if value is not None:
                os.environ[key] = value
        if os.getenv("EXAM_INTELLIGENCE_EVALUATION_MODE") != "true":
            raise RuntimeError("Evaluation environment marker is missing")
        return
    load_dotenv()
