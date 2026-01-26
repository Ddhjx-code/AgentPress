"""
Pytest configuration and fixtures for AgentPress testing
"""
import pytest
import os
from pathlib import Path
from dotenv import load_dotenv


@pytest.fixture(scope="session")
def test_data_dir():
    """Directory containing test data files"""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def sample_pdf_path(test_data_dir):
    """Path to sample PDF for testing"""
    pdf_path = test_data_dir / "sample_chapter.pdf"
    # Since we don't want to commit PDF files, we'll check if available
    # and create a sample if needed for integration tests
    if not pdf_path.exists():
        # Create a simple markdown as placeholder in fixtures
        placeholder_file = test_data_dir / "sample_content.md"
        if not placeholder_file.exists():
            placeholder_file.write_text("""
# Sample Text Content for Testing

This is a sample content that would normally come from a PDF file for testing the literary analysis system.

It contains various elements that the system should be able to analyze:

## Narrative Structure

The story begins and develops with certain pace and rhythm.

## Dialogue

"Hello," said the character. "How are you doing today?"

## Character Development

The character showed growth from the beginning to the end of the brief description.

## Literary Techniques

Some literary techniques are demonstrated in the brief text above.

""", encoding='utf-8')
    return pdf_path if pdf_path.exists() else None


@pytest.fixture(autouse=True)
def load_environment():
    """Load environment for all tests"""
    load_dotenv()
    # Set a test-specific API key if needed for tests that require it
    os.environ.setdefault("QWEN_API_KEY", "test-key-for-validation")