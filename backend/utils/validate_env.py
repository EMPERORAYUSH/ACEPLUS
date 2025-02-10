from typing import List
import ast
from dotenv import load_dotenv
import os

load_dotenv()

def validate_env_config() -> List[str]:
    """
    Validate all required environment variables before initializing any clients.
    Returns a list of valid provider names.
    Raises ValueError if any required configuration is missing or invalid.
    """
    valid_providers = []
    # Find all potential providers by looking for *_API_KEY pattern
    for key in os.environ:
        if key.endswith('_API_KEY'):
            provider = key.replace('_API_KEY', '')
            if provider:
                # Validate base URL exists
                base_url = os.environ.get(f'{provider}_BASE_URL')
                if not base_url:
                    raise ValueError(f"Missing base URL for provider: {provider}")

                # Validate models configuration
                models_str = os.environ.get(f'{provider}_MODELS')
                if not models_str:
                    raise ValueError(f"Missing models configuration for provider: {provider}")

                try:
                    models = ast.literal_eval(models_str)
                    if not isinstance(models, list) or not models:
                        raise ValueError(f"Invalid models configuration for provider: {provider}")
                except Exception as e:
                    raise ValueError(f"Error parsing models for provider {provider}: {str(e)}")

                # Check additional keys if they exist
                i = 2
                while True:
                    key = f"{provider}_API_KEY_{i}"
                    base_url_key = f"{provider}_BASE_URL_{i}"
                    
                    api_key = os.environ.get(key)
                    base_url = os.environ.get(base_url_key)
                    
                    # Break if no more keys found
                    if not api_key:
                        break
                    
                    # Validate base URL exists for additional key
                    if not base_url:
                        raise ValueError(f"Missing base URL for API key: {key}")
                    
                    i += 1

                valid_providers.append(provider)

    if not valid_providers:
        raise ValueError("No valid API providers found. Please check your environment variables.")

    # Validate specific use case configurations
    image_provider = os.environ.get('IMAGE_MODEL_PROVIDER', '').upper()
    image_model = os.environ.get('IMAGE_MODEL')
    if not image_provider or not image_model:
        raise ValueError("IMAGE_MODEL_PROVIDER and IMAGE_MODEL must be configured")
    if image_provider not in valid_providers:
        raise ValueError(f"IMAGE_MODEL_PROVIDER '{image_provider}' is not a valid provider")

    perf_provider = os.environ.get('PERFORMANCE_MODEL_PROVIDER', '').upper()
    perf_model = os.environ.get('PERFORMANCE_MODEL')
    if not perf_provider or not perf_model:
        raise ValueError("PERFORMANCE_MODEL_PROVIDER and PERFORMANCE_MODEL must be configured")
    if perf_provider not in valid_providers:
        raise ValueError(f"PERFORMANCE_MODEL_PROVIDER '{perf_provider}' is not a valid provider")

    return valid_providers
