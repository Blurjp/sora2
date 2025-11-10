#!/usr/bin/env python3
"""
Patch Open-Sora inference configs to use a valid Hugging Face checkpoint path.
It replaces local './ckpts/...' references with a HF path of the form
  org/repo/filename
Default: hpcai-tech/OpenSora-STDiT-v3/model.safetensors
Override with env CHECKPOINT_PATH if needed.
"""
import os
import re
import site
from pathlib import Path
from typing import Optional

def find_inference_config_dir() -> Optional[Path]:
    # Try installed package locations
    for sp in list(site.getsitepackages()) + [site.getusersitepackages()]:
        p = Path(sp) / "opensora" / "configs" / "diffusion" / "inference"
        if p.exists():
            return p
    # Try OPENSORA_PATH checkout
    root = os.environ.get("OPENSORA_PATH")
    if root:
        p = Path(root) / "configs" / "diffusion" / "inference"
        if p.exists():
            return p
    return None

def patch_file(path: Path, checkpoint: str) -> bool:
    text = path.read_text()
    if checkpoint in text:
        print(f"[OK] {path.name}: already uses {checkpoint}")
        return True
    orig = text
    # ckpt = './ckpts/xxx.safetensors'
    text = re.sub(r"ckpt\s*=\s*['\"]\./ckpts/[^'\"]+['\"]",
                  f'ckpt="{checkpoint}"', text)
    # checkpoint_path = './ckpts/xxx.safetensors'
    text = re.sub(r"checkpoint[_-]?path\s*=\s*['\"]\./ckpts/[^'\"]+['\"]",
                  f'checkpoint_path="{checkpoint}"', text, flags=re.IGNORECASE)
    if text != orig:
        path.write_text(text)
        print(f"[OK] {path.name}: patched to {checkpoint}")
        return True
    else:
        print(f"[WARN] {path.name}: no './ckpts/...' reference found")
        return False

def main() -> None:
    cfg_dir = find_inference_config_dir()
    if not cfg_dir:
        print("ERROR: Could not locate Open-Sora inference configs")
        raise SystemExit(1)

    checkpoint = os.environ.get(
        "CHECKPOINT_PATH",
        "hpcai-tech/OpenSora-STDiT-v3/model.safetensors",
    )
    print(f"Config dir: {cfg_dir}")
    print(f"Checkpoint: {checkpoint}")

    any_ok = False
    for name in ("256px.py", "768px.py"):
        p = cfg_dir / name
        if p.exists():
            any_ok = patch_file(p, checkpoint) or any_ok
        else:
            print(f"[WARN] missing: {p}")

    if not any_ok:
        print("ERROR: No configs updated; please verify the files contain './ckpts/' paths.")
        raise SystemExit(1)

if __name__ == "__main__":
    main()
