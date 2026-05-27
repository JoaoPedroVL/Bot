#!/usr/bin/env python3
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Nao e mais necessario processar o PDF.")
    logger.info("O bot le diretamente o arquivo edital.md.")


if __name__ == "__main__":
    main()
