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
    orig = text
    changes_made = []

    # Check if already patched
    if (checkpoint in text and
        'google/t5-v1_1-xxl' in text and
        'openai/clip-vit-large-patch14' in text and
        './ckpts/' not in text):
        print(f"[OK] {path.name}: already patched with correct paths")
        return True

    # Pattern 1: Fix VAE path - hunyuan_vae.safetensors
    vae_pattern = r'from_pretrained\s*=\s*["\']\.\/ckpts\/hunyuan_vae\.safetensors["\']'
    if re.search(vae_pattern, text):
        text = re.sub(vae_pattern,
                     'from_pretrained="hpcai-tech/Open-Sora-v2", subfolder="hunyuan_vae"',
                     text)
        changes_made.append("VAE")

    # Pattern 2: Fix T5 text encoder path
    t5_pattern = r'from_pretrained\s*=\s*["\']\.\/ckpts\/google\/t5-v1_1-xxl["\']'
    if re.search(t5_pattern, text):
        text = re.sub(t5_pattern,
                     'from_pretrained="google/t5-v1_1-xxl"',
                     text)
        changes_made.append("T5")

    # Pattern 3: Fix CLIP text encoder path
    clip_pattern = r'from_pretrained\s*=\s*["\']\.\/ckpts\/openai\/clip-vit-large-patch14["\']'
    if re.search(clip_pattern, text):
        text = re.sub(clip_pattern,
                     'from_pretrained="openai/clip-vit-large-patch14"',
                     text)
        changes_made.append("CLIP")

    # Pattern 4: Fix main model path - Open_Sora_v2.safetensors
    model_pattern = r'from_pretrained\s*=\s*["\']\.\/ckpts\/Open_Sora_v2\.safetensors["\']'
    if re.search(model_pattern, text):
        text = re.sub(model_pattern,
                     'from_pretrained="hpcai-tech/Open-Sora-v2", subfolder="model"',
                     text)
        changes_made.append("Model")

    # Pattern 5: Fix any remaining ./ckpts/ references generically
    generic_ckpts = r'from_pretrained\s*=\s*["\']\.\/ckpts\/[^"\']+["\']'
    if re.search(generic_ckpts, text):
        text = re.sub(generic_ckpts, f'from_pretrained="{checkpoint}"', text)
        if "generic" not in changes_made:
            changes_made.append("generic paths")

    # Pattern 6: Legacy ckpt= and checkpoint_path= patterns
    text = re.sub(r"ckpt\s*=\s*['\"]\./ckpts/[^'\"]+['\"]",
                  f'ckpt="{checkpoint}"', text)
    text = re.sub(r"checkpoint[_-]?path\s*=\s*['\"]\./ckpts/[^'\"]+['\"]",
                  f'checkpoint_path="{checkpoint}"', text, flags=re.IGNORECASE)

    if text != orig:
        path.write_text(text)
        components = ", ".join(changes_made) if changes_made else "paths"
        print(f"[OK] {path.name}: fixed {components}")
        return True
    else:
        print(f"[WARN] {path.name}: no patterns matched")
        relevant_lines = [line for line in text.split('\n')
                         if 'ckpt' in line.lower() or 'from_pretrained' in line.lower()]
        if relevant_lines:
            print(f"  Current checkpoint-related lines:")
            for line in relevant_lines[:10]:
                print(f"    {line.strip()}")
        return False

def main() -> None:
    cfg_dir = find_inference_config_dir()
    if not cfg_dir:
        print("ERROR: Could not locate Open-Sora inference configs")
        raise SystemExit(1)

    checkpoint = os.environ.get(
        "CHECKPOINT_PATH",
        "hpcai-tech/Open-Sora-v2/Open_Sora_v2.safetensors",
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
