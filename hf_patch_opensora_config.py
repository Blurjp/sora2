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

    # Pattern 1: ckpt = './ckpts/xxx.safetensors'
    text = re.sub(r"ckpt\s*=\s*['\"]\./ckpts/[^'\"]+['\"]",
                  f'ckpt="{checkpoint}"', text)

    # Pattern 2: checkpoint_path = './ckpts/xxx.safetensors'
    text = re.sub(r"checkpoint[_-]?path\s*=\s*['\"]\./ckpts/[^'\"]+['\"]",
                  f'checkpoint_path="{checkpoint}"', text, flags=re.IGNORECASE)

    # Pattern 3: from_pretrained with old incorrect checkpoint paths
    # Replace from_pretrained="hpcai-tech/OpenSora-STDiT-v3" with full path
    text = re.sub(r'from_pretrained\s*=\s*["\']hpcai-tech/OpenSora-STDiT-v3["\']',
                  f'from_pretrained="{checkpoint}"', text)
    text = re.sub(r'from_pretrained\s*=\s*["\']hpcai-tech/Open-Sora-v2["\']',
                  f'from_pretrained="{checkpoint}"', text)

    # Pattern 4: Old ckpt= paths (without /model.safetensors)
    text = re.sub(r"ckpt\s*=\s*['\"]hpcai-tech/OpenSora-STDiT-v3['\"]",
                  f'ckpt="{checkpoint}"', text)
    text = re.sub(r"ckpt\s*=\s*['\"]hpcai-tech/Open-Sora-v2['\"]",
                  f'ckpt="{checkpoint}"', text)

    if text != orig:
        path.write_text(text)
        changes = len([1 for i, j in zip(orig.split('\n'), text.split('\n')) if i != j])
        print(f"[OK] {path.name}: patched {changes} lines with {checkpoint}")
        return True
    else:
        # Show what's actually in the file for debugging
        print(f"[WARN] {path.name}: no patterns matched")
        relevant_lines = [line for line in text.split('\n')
                         if 'ckpt' in line.lower() or 'from_pretrained' in line.lower()]
        if relevant_lines:
            print(f"  Current checkpoint-related lines:")
            for line in relevant_lines[:10]:  # Show first 10 matches
                print(f"    {line.strip()}")
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
