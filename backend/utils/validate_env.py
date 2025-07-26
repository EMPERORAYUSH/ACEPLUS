from typing import List
import json
from dotenv import dotenv_values
import os

def validate_env_config() -> List[str]:
    """
    Validate all required environment variables based on the new .env structure.
    Returns a list of valid provider names.
    Raises ValueError if any required configuration is missing or invalid.
    """
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if not os.path.exists(env_path):
        raise ValueError("Missing .env file in backend directory")
        
    env_vars = dotenv_values(env_path)

    # 1. Validate PROVIDERS
    providers_str = env_vars.get("PROVIDERS")
    if not providers_str:
        raise ValueError("PROVIDERS environment variable is not set.")
    try:
        providers = json.loads(providers_str)
        if not isinstance(providers, list) or not all(isinstance(p, str) for p in providers):
            raise ValueError("PROVIDERS must be a JSON array of strings.")
    except json.JSONDecodeError:
        raise ValueError("PROVIDERS environment variable is not a valid JSON array.")

    # 2. Validate each provider's config
    for provider in providers:
        if not env_vars.get(f'{provider}_API_KEY'):
            raise ValueError(f"Missing API key for provider: {provider}")
        if not env_vars.get(f'{provider}_BASE_URL'):
            raise ValueError(f"Missing base URL for provider: {provider}")

        # Check for additional keys and their URLs
        i = 2
        while True:
            api_key = env_vars.get(f"{provider}_API_KEY_{i}")
            base_url = env_vars.get(f"{provider}_BASE_URL_{i}")
            if not api_key:
                break
            if not base_url:
                raise ValueError(f"Missing base URL for API key: {provider}_API_KEY_{i}")
            i += 1
            
    # 3. Validate Model Assignments
    model_assignments = [
    "IMAGE_MODELS",
    "HINT_MODELS",
    "SOLUTION_MODELS",
    "PERFORMANCE_ANALYSIS_MODELS"
]
    for assignment in model_assignments:
        models_str = env_vars.get(assignment)
        if not models_str:
            raise ValueError(f"Missing model assignment environment variable: {assignment}")
        
        try:
            models = json.loads(models_str)
            if not isinstance(models, list) or not models:
                raise ValueError(f"{assignment} must be a non-empty JSON array of strings.")
            
            for model_full_name in models:
                if not isinstance(model_full_name, str) or '/' not in model_full_name:
                    raise ValueError(f"Invalid model format in {assignment}: '{model_full_name}'. Expected 'PROVIDER/model_name'.")
                
                model_provider = model_full_name.split('/')[0]
                if model_provider not in providers:
                    raise ValueError(f"Provider '{model_provider}' from {assignment} is not listed in PROVIDERS.")
        except json.JSONDecodeError:
            raise ValueError(f"{assignment} environment variable is not a valid JSON array.")
        except ValueError as e:
            raise e

    return providers
