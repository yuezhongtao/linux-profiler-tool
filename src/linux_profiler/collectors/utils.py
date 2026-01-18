"""Utility functions for collectors."""


def bytes_to_human(bytes_value: int | float) -> str:
    """Convert bytes to human-readable format.
    
    Args:
        bytes_value: The number of bytes to convert
        
    Returns:
        Human-readable string representation (e.g., "1.5 GB")
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"
