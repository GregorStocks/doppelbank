import uvicorn


def main() -> None:
    uvicorn.run("doppelbank.veneer.app:app", host="127.0.0.1", port=8082, reload=True)


if __name__ == "__main__":
    main()
