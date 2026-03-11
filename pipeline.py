import os
import json
import importlib
import logging
from typing import Dict


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_config(config_path: str = 'config.json') -> Dict:
    with open(config_path, 'r') as f:
        return json.load(f)


def run_pipeline(config: Dict) -> None:
    """Pipeline: config → sources → outputs."""
    required_env = config['pipeline']['required_env']
    for var in required_env:
        if not os.environ.get(var):
            raise ValueError(f"Missing env var: {var}")

    # === SOURCES PHASE ===
    ioc_store = {}
    pipeline_config = config['pipeline']

    for src_config in pipeline_config['sources']:
        source_type = src_config['type']
        logger.info(f"Loading source {source_type}")
        module = importlib.import_module(f'sources.{source_type}')
        source_class = getattr(module, source_type.title())
        source = source_class(src_config)

        source_names = src_config['name']
        for source_name in (source_names if isinstance(source_names, list) else [source_names]):
            logger.info(f"Processing yara rule {source_name}")
            hash_domains = source.load_iocs(source_name, limit=pipeline_config.get('limit', 20))
            ioc_store[source_name] = hash_domains

    logger.info(f"Pipeline complete: {sum(len(hm) for hm in ioc_store.values())} hash-domain pairs")

    # === OUTPUTS PHASE ===
    for out_config in pipeline_config['outputs']:
        output_type = out_config['type']
        logger.info(f"Storing to {output_type}")

        module = importlib.import_module(f'outputs.{output_type}')
        output_class = getattr(module, output_type.title())
        output = output_class(out_config)

        result = output.store(ioc_store)
        logger.info(f"{output_type} stored: {result.get('id', 'OK')}")


def main():
    config = load_config()
    run_pipeline(config)


if __name__ == "__main__":
    main()
