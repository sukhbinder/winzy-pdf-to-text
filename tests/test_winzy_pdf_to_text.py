import pytest
import winzy_pdf_to_text as w
from argparse import ArgumentParser
from unittest.mock import MagicMock, mock_open
import io
import os
import time


def test_create_parser():
    subparser = ArgumentParser().add_subparsers()
    parser = w.create_parser(subparser)
    assert parser is not None
    result, _ = parser.parse_known_args(["hello", "-p", "1-4"])
    assert result.file_path == "hello"
    assert result.pages == ["1-4"]


def test_pdf_to_text_local_file(monkeypatch):
    # Mock pypdf.PdfReader
    mock_reader_instance = MagicMock()
    mock_reader_instance.pages = [MagicMock(), MagicMock()]
    mock_reader_instance.pages[0].extract_text.return_value = "Page 1 text."
    mock_reader_instance.pages[1].extract_text.return_value = "Page 2 text."
    mock_pdf_reader = MagicMock(return_value=mock_reader_instance)
    monkeypatch.setattr(w.pypdf, "PdfReader", mock_pdf_reader)

    # Mock open for local file reading
    monkeypatch.setattr("builtins.open", mock_open(read_data=b"dummy pdf content"))

    # Test without page range
    result = w.pdf_to_text("dummy.pdf")
    assert result == "Page 1 text.\nPage 2 text."

    # Test with page range
    result_range = w.pdf_to_text("dummy.pdf", page_range="1-2")
    assert result_range == "Page 1 text.\nPage 2 text."

    result_single_page = w.pdf_to_text("dummy.pdf", page_range="2")
    assert result_single_page == "Page 2 text."


def test_pdf_to_text_url(monkeypatch):
    # Mock fetch_pdf_with_cache to return a dummy PDF BytesIO object
    dummy_pdf_content = io.BytesIO(b"dummy pdf content")
    mock_fetch = MagicMock(return_value=dummy_pdf_content)
    monkeypatch.setattr(w, "fetch_pdf_with_cache", mock_fetch)

    # Mock pypdf.PdfReader
    mock_reader_instance = MagicMock()
    mock_reader_instance.pages = [MagicMock()]
    mock_reader_instance.pages[0].extract_text.return_value = "Text from URL PDF."
    mock_pdf_reader = MagicMock(return_value=mock_reader_instance)
    monkeypatch.setattr(w.pypdf, "PdfReader", mock_pdf_reader)

    result = w.pdf_to_text("http://example.com/dummy.pdf")
    mock_fetch.assert_called_once_with("http://example.com/dummy.pdf")
    assert result == "Text from URL PDF."


def test_fetch_pdf_with_cache(monkeypatch):
    url = "http://example.com/test.pdf"

    # Mock os and os.path functions
    mock_makedirs = MagicMock()
    monkeypatch.setattr(w.os, "makedirs", mock_makedirs)

    # Since get_cache_filename uses os.path.join, we can just mock that
    # to return a predictable path, avoiding issues with `~`.
    cache_file_path = "/tmp/pdf_cache/test.pdf"
    monkeypatch.setattr(
        w, "get_cache_filename", MagicMock(return_value=cache_file_path)
    )

    mock_exists = MagicMock(return_value=False)
    monkeypatch.setattr(w.os.path, "exists", mock_exists)

    mock_requests_get = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "application/pdf"}
    mock_response.content = b"new pdf data"
    mock_requests_get.return_value = mock_response
    monkeypatch.setattr(w.requests, "get", mock_requests_get)

    mock_file = mock_open()
    monkeypatch.setattr("builtins.open", mock_file)

    # --- Test Case 1: No cache, download ---
    w.fetch_pdf_with_cache(url)

    mock_exists.assert_called_with(cache_file_path)
    mock_requests_get.assert_called_once()
    mock_file.assert_called_with(cache_file_path, "wb")
    mock_file().write.assert_called_once_with(b"new pdf data")

    # --- Test Case 2: Cache exists and is valid ---
    mock_exists.return_value = True
    mock_getmtime = MagicMock(return_value=time.time() - 100)  # recent file
    monkeypatch.setattr(w.os.path, "getmtime", mock_getmtime)

    mock_requests_get.reset_mock()

    # mock open to return some cached data
    cached_data = b"cached pdf data"
    monkeypatch.setattr("builtins.open", mock_open(read_data=cached_data))

    pdf_file = w.fetch_pdf_with_cache(url)

    assert pdf_file.read() == cached_data
    mock_requests_get.assert_not_called()

    # --- Test Case 3: Cache exists but is expired ---
    mock_getmtime.return_value = time.time() - (w.CACHE_DURATION + 100)  # expired file

    mock_requests_get.reset_mock()
    mock_open_instance = mock_open()
    monkeypatch.setattr("builtins.open", mock_open_instance)

    w.fetch_pdf_with_cache(url)

    mock_requests_get.assert_called_once()
    mock_open_instance.assert_called_with(cache_file_path, "wb")
    mock_open_instance().write.assert_called_once_with(b"new pdf data")


def test_plugin_run(monkeypatch, capsys):
    # Mock the pdf_to_text function to avoid actual processing
    mock_pdf_to_text = MagicMock(return_value="Mocked PDF text")
    monkeypatch.setattr(w, "pdf_to_text", mock_pdf_to_text)

    # Create a mock args object
    mock_args = MagicMock()
    mock_args.file_path = "dummy.pdf"
    mock_args.pages = None

    # Test run without pages
    w.pdf2txt_plugin.run(mock_args)
    mock_pdf_to_text.assert_called_with("dummy.pdf")
    captured = capsys.readouterr()
    assert "Mocked PDF text" in captured.out

    # Test run with pages
    mock_args.pages = ["1-3"]
    w.pdf2txt_plugin.run(mock_args)
    mock_pdf_to_text.assert_called_with("dummy.pdf", "1-3")
