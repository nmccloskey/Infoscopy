from __future__ import annotations

import zipfile
from datetime import datetime
from io import BytesIO
from pathlib import Path

import streamlit as st

from psair import __version__
from psair.webapp.manual_viewer import render_manual_ui


def zip_folder(folder_path: Path) -> BytesIO:
    """Compress a folder into an in-memory ZIP buffer."""
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in folder_path.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(folder_path)
                zf.write(file_path, arcname)

    zip_buffer.seek(0)
    return zip_buffer


def get_repo_root() -> Path:
    """
    Return the repository root containing the external docs/ manuals.

    The hosted app is launched from the repository root, while local imports may
    resolve this module from src/psair/webapp. Check both locations so docs/
    does not need to be bundled into the installed package.
    """
    module_root = Path(__file__).resolve().parents[3]
    for candidate in (Path.cwd(), module_root):
        has_docs = (candidate / "docs").is_dir()
        has_launcher = (candidate / "streamlit_app.py").exists()
        if has_docs and has_launcher:
            return candidate.resolve()
    return module_root


def main() -> None:
    """Run the PSAIR Streamlit app."""
    start_time = datetime.now()
    repo_root = get_repo_root()

    st.set_page_config(
        page_title="PSAIR Web App",
        page_icon="📘",
        layout="wide",
    )

    st.title("PSAIR Web App")
    st.subheader(
        "Python Scaffolding for Analysis Itineraries in Research"
    )
    st.caption(f"Version: {__version__}")

    st.subheader(
        "PSAIR Manual"
    )
    render_manual_ui(
        repo_root=repo_root,
        manual_rel_dir="docs/psair_manual",
        pdf_yaml_rel_path="docs/psair_manual/psair_manual_pdf.yaml",
        expander_label="📘 Show / Hide PSAIR Manual Menu",
        ui_key="psair_manual",
        enable_pdf_export=True,
    )

    # Placeholder body content
    st.markdown("---")
    st.write("Welcome to the PSAIR web app.")

    elapsed = datetime.now() - start_time
    st.caption(f"App loaded in {elapsed.total_seconds():.2f} seconds.")


if __name__ == "__main__":
    main()
