import tempfile
import time
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import importlib
convert_pdf = importlib.import_module("convert-pdf")


def benchmark(num_pages=100, page_size_kb=500):
    print(f"Running benchmark with {num_pages} pages ({page_size_kb}KB per page)...")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        page_bytes = b"X" * (page_size_kb * 1024)
        pages = []
        for i in range(num_pages):
            p = tmp_path / f"page-{i:03d}.png"
            p.write_bytes(page_bytes)
            pages.append(str(p))

        assets_dir = tmp_path / "assets"
        assets_dir.mkdir()

        # External assets
        t0 = time.perf_counter()
        slides_ext = convert_pdf.process_pages(pages, external_assets=True, assets_dir=assets_dir)
        t_ext = time.perf_counter() - t0

        # Inline base64
        t0 = time.perf_counter()
        slides_in = convert_pdf.process_pages(pages, external_assets=False, assets_dir=None)
        t_in = time.perf_counter() - t0

        print(f"External assets time: {t_ext*1000:.2f} ms")
        print(f"Inline base64 time:    {t_in*1000:.2f} ms")
        return t_ext, t_in


if __name__ == "__main__":
    benchmark()
