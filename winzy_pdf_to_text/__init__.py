import winzy
import pypdf
from urllib.parse import urlparse
import requests
from io import BytesIO
import os
import hashlib
import time


CACHE_DIR = "~/pdf_cache"
CACHE_DURATION = 24 * 60 * 60


def get_cache_filename(url):
    """Generate a cache file path based on the URL's filename."""
    os.makedirs(CACHE_DIR, exist_ok=True)  # Ensure cache directory exists
    filename = os.path.basename(url)
    if not filename.endswith(".pdf"):
        # Fallback to hashed filename if URL doesn't end with a proper name
        filename = hashlib.md5(url.encode()).hexdigest() + ".pdf"
    return os.path.join(CACHE_DIR, filename)


def fetch_pdf_with_cache(url, cache_duration=CACHE_DURATION):
    """Fetch PDF from URL with per-URL caching."""
    cache_file = get_cache_filename(url)

    # Check if cache is valid
    if os.path.exists(cache_file):
        last_modified = os.path.getmtime(cache_file)
        if time.time() - last_modified < cache_duration:
            print(f"Using cached PDF: {cache_file}")
            with open(cache_file, "rb") as f:
                return BytesIO(f.read())
        else:
            print(f"Cache expired for {cache_file}. Downloading new PDF.")
    else:
        print(f"No cache found for {url}. Downloading PDF.")

    # Download PDF
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Referer": "https://www.bseindia.com/",
        "Accept": "application/pdf",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200 and response.headers.get(
        "Content-Type", ""
    ).startswith("application/pdf"):
        with open(cache_file, "wb") as f:
            f.write(response.content)
        return BytesIO(response.content)
    else:
        raise Exception(f"Failed to fetch PDF: {response.status_code}")


def pdf_to_text(file_path_or_url, page_range=None):
    """Convert PDF to text from a file path or URL"""
    parsed = urlparse(file_path_or_url)
    is_url = parsed.scheme in ("http", "https")

    if is_url:
        file = fetch_pdf_with_cache(file_path_or_url)
    else:
        file = open(file_path_or_url, "rb")

    with file:
        reader = pypdf.PdfReader(file)
        pages = [page.extract_text() for page in reader.pages]

        if page_range:
            if "-" in page_range:
                start, end = map(int, page_range.split("-"))
            else:
                start = end = int(page_range)
            return "\n".join(pages[start - 1 : end])
        else:
            return "\n".join(pages)

    file.close()


def create_parser(subparser):
    parser = subparser.add_parser(
        "pdf2txt", description="Extract text from a given pdf"
    )
    # Add subprser arguments here.
    parser.add_argument("file_path", type=str, help="Path to the PDF file")
    parser.add_argument(
        "-p",
        "--pages",
        type=str,
        nargs="+",
        help="Page numbers to extract example: 1-4 for  1 to 4. or just a single page",
    )

    return parser


class HelloWorld:
    """An example plugin"""

    __name__ = "pdf2txt"

    @winzy.hookimpl
    def register_commands(self, subparser):
        parser = create_parser(subparser)
        parser.set_defaults(func=self.run)

    def run(self, args):
        pdf_path = args.file_path
        if args.pages:
            print(pdf_to_text(pdf_path, ",".join(args.pages)))
        else:
            print(pdf_to_text(pdf_path))

    def hello(self, args):
        # this routine will be called when "winzy "pdf2txt is called."
        print("Hello! This is an example ``winzy`` plugin.")


pdf2txt_plugin = HelloWorld()
