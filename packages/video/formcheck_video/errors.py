class VideoTechnicalError(Exception):
    """Tool or parse failure. ``safe_message`` never includes a source path."""

    def __init__(self, safe_message: str) -> None:
        super().__init__(safe_message)
        self.safe_message = safe_message
        self.code = "VIDEO_TECHNICAL"
