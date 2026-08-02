from pathlib import Path

_original_read_text = Path.read_text


def _read_text(self: Path, *args, **kwargs):
    if self.name == "part-009b.b64":
        first = _original_read_text(self.with_name("part-009b1.b64"), *args, **kwargs).strip()
        second = _original_read_text(self.with_name("part-009b2.b64"), *args, **kwargs).strip()
        return first + second
    return _original_read_text(self, *args, **kwargs)


Path.read_text = _read_text
