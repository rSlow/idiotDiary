__all__ = (
    "n_text",
)


def n_text(obj: str):
    return "".join([let for let in obj if let.isascii() or let.isalnum()]).strip()
