from loguru import logger


def setup_logger(file_path: str) -> None:
    """
    Sets up the logger with the given file path.

    Parameters
    ----------
    file_path : str
        The path to the log file.

    Returns
    -------
    None
    """
    logger.remove(0)
    logger.add(
        file_path,
        format="{time: MMMM D, YYYY - HH:mm:ss} {level} <green>{message}</green>",
        level="INFO"
    )
