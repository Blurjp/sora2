#!/usr/bin/env python3
"""
Patch Open-Sora inference configs to point each component at the correct
Hugging Face repo/file. Handles legacy ./ckpts paths, subfolder references,
and previously incorrect OpenSora-STDiT-v3 tree URLs.
"""

import os
import re
import sys
from pathlib import Path
import site

MODEL_PATH = "hpcai-tech/OpenSora-STDiT-v3/model.safetensors"
VAE_PATH = "hpcai-tech/Open-Sora-v2/hunyuan_vae.safetensors"
T5_PATH = "google/t5-v1_1-xxl"
CLIP_PATH = "openai/clip-vit-large-patch14"


def find_config_dir() -> Path | None:
    """Locate the Open-Sora configs directory."""
    opensora_path = os.environ.get("OPENSORA_PATH")
    if opensora_path:
        cfg = Path(opensora_path) / "configs" / "diffusion" / "inference"
        if cfg.exists():
            return cfg

    candidates = [
        Path.home() / "Open-Sora" / "configs" / "diffusion" / "inference",
        Path("/opt/Open-Sora/configs/diffusion/inference"),
        Path("/home/ubuntu/Open-Sora/configs/diffusion/inference"),
    ]

    for path in candidates:
        if path.exists():
            return path

    for sp in list(site.getsitepackages()) + [site.getusersitepackages()]:
        if sp:
            cfg = Path(sp) / "opensora" / "configs" / "diffusion" / "inference"
            if cfg.exists():
                return cfg

    return None


def apply_replacements(text: str) -> tuple[str, int]:
    """Run all regex replacements and report how many edits were made."""
    replacements = [
        (r"\./ckpts/Open_Sora_v2\.safetensors", MODEL_PATH, "model ./ckpts path"),
        (r"hpcai-tech/Open-Sora-v2/model", MODEL_PATH, "model subfolder reference"),
        (r"hpcai-tech/OpenSora-STDiT-v3/tree/main/model\.safetensors", MODEL_PATH, "model tree URL"),
        (
            r'from_pretrained\s*=\s*["\']hpcai-tech/Open-Sora-v2[^"\']*["\']\s*,\s*subfolder\s*=\s*["\']model["\']',
            f'from_pretrained="{MODEL_PATH}"',
            "model subfolder block",
        ),
        (r"\./ckpts/hunyuan_vae\.safetensors", VAE_PATH, "VAE ./ckpts path"),
        (r"hpcai-tech/OpenSora-STDiT-v3/hunyuan_vae\.safetensors", VAE_PATH, "VAE wrong repo"),
        (
            r'from_pretrained\s*=\s*["\']hpcai-tech/Open-Sora-v2[^"\']*["\']\s*,\s*subfolder\s*=\s*["\']hunyuan_vae["\']',
            f'from_pretrained="{VAE_PATH}"',
            "VAE subfolder block",
        ),
        (r"\./ckpts/google/t5-v1_1-xxl", T5_PATH, "T5 ./ckpts path"),
        (
            r'from_pretrained\s*=\s*["\']hpcai-tech/Open-Sora-v2[^"\']*["\']\s*,\s*subfolder\s*=\s*["\']google/t5-v1_1-xxl["\']',
            f'from_pretrained="{T5_PATH}"',
            "T5 subfolder block",
        ),
        (r"\./ckpts/openai/clip-vit-large-patch14", CLIP_PATH, "CLIP ./ckpts path"),
        (
            r'from_pretrained\s*=\s*["\']hpcai-tech/Open-Sora-v2[^"\']*["\']\s*,\s*subfolder\s*=\s*["\']openai/clip-vit-large-patch14["\']',
            f'from_pretrained="{CLIP_PATH}"',
            "CLIP subfolder block",
        ),
    ]

    total_changes = 0
    for pattern, replacement, desc in replacements:
        text, count = re.subn(pattern, replacement, text, flags=re.MULTILINE)
        if count:
            total_changes += count
            print(f"  ✓ {desc}: {count} change(s)")

    return text, total_changes


def patch_config_file(file_path: Path) -> bool:
    """Patch a single config file."""
    if not file_path.exists():
        print(f"Skipping {file_path} (not found)")
        return False

    print(f"\nPatching {file_path}...")
    content = file_path.read_text()
    new_content, changes = apply_replacements(content)

    if not changes:
        print("  • No replacements needed")
        return False

    backup = file_path.with_suffix(file_path.suffix + ".backup")
    if not backup.exists():
        backup.write_text(content)
        print(f"  ✓ Backup saved: {backup.name}")

    file_path.write_text(new_content)
    print(f"  ✓ Updated {changes} segment(s)")
    return True


def main():
    print("=" * 70)
    print("Open-Sora Component Config Patcher")
    print("=" * 70)
    print()
    print("Targets:")
    print(f"  - Model : {MODEL_PATH}")
    print(f"  - VAE   : {VAE_PATH}")
    print(f"  - T5    : {T5_PATH}")
    print(f"  - CLIP  : {CLIP_PATH}")
    print()

    config_dir = find_config_dir()
    if not config_dir:
        print("ERROR: Could not locate Open-Sora inference configs.")
        print("Set OPENSORA_PATH or install open-sora in the current environment.")
        sys.exit(1)

    print(f"Config directory: {config_dir}")

    any_changes = False
    for name in ("256px.py", "768px.py"):
        path = config_dir / name
        if path.exists():
            any_changes |= patch_config_file(path)
        else:
            print(f"Skipping missing config: {path}")

    if not any_changes:
        print("\nNo changes were required; configs already point to the correct Hugging Face paths.")
    else:
        print("\nDone! Restart the GPU service so the new paths take effect.")


if __name__ == "__main__":
    main()
