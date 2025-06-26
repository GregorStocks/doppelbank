import uvicorn

from doppelbank.lib.logging_config import configure_logging


def main() -> None:
    # Configure logging to show INFO level messages by default
    configure_logging(module_name="veneer")

    uvicorn.run(
        "doppelbank.veneer.app:app",
        host="127.0.0.1",
        port=8082,
        reload=True,
    )


if __name__ == "__main__":
    main()
