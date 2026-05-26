"""Deploy project files to the Hugging Face Space (requires Classic WRITE token)."""
import os
import sys
from huggingface_hub import HfApi

REPO_ID = "ynchzx/techcorp-support-agent"
IGNORE = [
    ".git/**",
    ".github/**",
    "data/chroma_db/**",
    "**/__pycache__/**",
    ".env",
    "deploy*.ps1",
    "scripts/**",
]


def main() -> None:
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    if not token:
        print("Set HF_TOKEN to a Classic WRITE token from https://huggingface.co/settings/tokens")
        sys.exit(1)

    api = HfApi(token=token)
    api.upload_folder(
        folder_path=".",
        repo_id=REPO_ID,
        repo_type="space",
        commit_message="Deploy TechCorp support agent",
        ignore_patterns=IGNORE,
    )
    print(f"Done: https://huggingface.co/spaces/{REPO_ID}")


if __name__ == "__main__":
    main()
