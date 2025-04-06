def main() -> None:
    import uvicorn

    uvicorn.run(
        "cleansales_backend.api.app:app", host="0.0.0.0", port=8888, reload=True
    )


if __name__ == "__main__":
    main()
