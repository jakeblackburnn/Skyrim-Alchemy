import sys
from pathlib import Path
from contextlib import contextmanager

RESULTS_DIR = Path(__file__).parent.parent / "results"


class _Tee:
    def __init__(self, *files): self.files = files
    def write(self, data):
        for f in self.files: f.write(data)
    def flush(self):
        for f in self.files: f.flush()


@contextmanager
def tee_stdout(path):
    with open(path, 'w') as txt_file:
        original = sys.stdout
        sys.stdout = _Tee(original, txt_file)
        try:
            yield
        finally:
            sys.stdout = original
