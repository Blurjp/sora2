#!/usr/bin/env python3
"""
Patch Open-Sora inference configs to use correct HuggingFace paths for each component.

This fixes the "Missing key(s) in state_dict" error by ensuring:
- Model (flux): hpcai-tech/Open-Sora-v2/Open_Sora_v2.safetensors
- VAE (hunyuan): hpcai-tech/Open-Sora-v2/hunyuan_vae.safetensors
- T5 text encoder: google/t5-v1_1-xxl
- CLIP text encoder: openai/clip-vit-large-patch14
"""
import os
import re
import sys
from pathlib import Path
import site


def find_config_dir():
    """Locate Open-Sora configs directory"""
    # Try OPENSORA_PATH environment variable first
    opensora_path = os.environ.get("OPENSORA_PATH")
    if opensora_path:
        p = Path(opensora_path) / "configs" / "diffusion" / "inference"
        if p.exists():
            return p

    # Try common locations
    common_paths = [
        Path.home() / "Open-Sora" / "configs" / "diffusion" / "inference",
        Path("/opt/Open-Sora/configs/diffusion/inference"),
        Path("/home/ubuntu/Open-Sora/configs/diffusion/inference"),
    ]

    for p in common_paths:
        if p.exists():
            return p

    # Try site-packages
    for sp in list(site.getsitepackages()) + [site.getusersitepackages()]:
        if sp:
            p = Path(sp) / "opensora" / "configs" / "diffusion" / "inference"
            if p.exists():
                return p

    return None


def patch_config_file(file_path):
    """Patch a single config file with correct HuggingFace paths"""
    if not file_path.exists():
        print(f"Skipping {file_path} (not found)")
        return False

    print(f"\nPatching {file_path}...")

    try:
        content = file_path.read_text()
        original = content

        # Create backup
        backup_path = file_path.with_suffix(file_path.suffix + '.backup')
        if not backup_path.exists():
            backup_path.write_text(original)
            print(f"  → Backup saved: {backup_path.name}")

        changes = []

        # 1. Patch main model checkpoint path (./ckpts/... to HF Hub)
        main_model_pattern = r'(["\'])\.\/ckpts\/[^"\']+\.safetensors\1'
        if re.search(main_model_pattern, content):
            content = re.sub(
                main_model_pattern,
                '"hpcai-tech/Open-Sora-v2/Open_Sora_v2.safetensors"',
                content
            )
            changes.append("main model checkpoint")

        # 2. Patch VAE to use hunyuan_vae.safetensors
        # Look for ae = dict(...from_pretrained=...,...)
        vae_pattern = r'(ae\s*=\s*dict\s*\([^)]*from_pretrained\s*=\s*)["\']([^"\']+)["\']'
        vae_match = re.search(vae_pattern, content, re.DOTALL)
        if vae_match:
            current_vae = vae_match.group(2)
            if 'hunyuan_vae' not in current_vae:
                content = re.sub(
                    vae_pattern,
                    r'\1"hpcai-tech/Open-Sora-v2/hunyuan_vae.safetensors"',
                    content,
                    flags=re.DOTALL
                )
                changes.append(f"VAE ({current_vae} → hunyuan_vae)")

        # 3. Patch T5 text encoder
        # Look for text_encoder with type="t5"
        t5_pattern = r'(text_encoder\s*=\s*dict\s*\([^)]*type\s*=\s*["\']t5["\'][^)]*from_pretrained\s*=\s*)["\']([^"\']+)["\']'
        t5_match = re.search(t5_pattern, content, re.DOTALL | re.IGNORECASE)
        if t5_match:
            current_t5 = t5_match.group(2)
            if 'google/t5' not in current_t5:
                content = re.sub(
                    t5_pattern,
                    r'\1"google/t5-v1_1-xxl"',
                    content,
                    flags=re.DOTALL | re.IGNORECASE
                )
                changes.append(f"T5 encoder ({current_t5} → google/t5-v1_1-xxl)")

        # 4. Patch CLIP text encoder
        # Look for text_encoder with type="clip"
        clip_pattern = r'(text_encoder\s*=\s*dict\s*\([^)]*type\s*=\s*["\']clip["\'][^)]*from_pretrained\s*=\s*)["\']([^"\']+)["\']'
        clip_match = re.search(clip_pattern, content, re.DOTALL | re.IGNORECASE)
        if clip_match:
            current_clip = clip_match.group(2)
            if 'openai/clip' not in current_clip:
                content = re.sub(
                    clip_pattern,
                    r'\1"openai/clip-vit-large-patch14"',
                    content,
                    flags=re.DOTALL | re.IGNORECASE
                )
                changes.append(f"CLIP encoder ({current_clip} → openai/clip-vit-large-patch14)")

        if content != original:
            file_path.write_text(content)
            print(f"  ✓ Patched: {', '.join(changes)}")
            return True
        else:
            print(f"  → Already correct or no matches found")
            return False

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def verify_hf_downloads():
    """Verify that models can be downloaded from HuggingFace"""
    print("\n" + "=" * 70)
    print("Verifying HuggingFace downloads...")
    print("=" * 70)

    try:
        from huggingface_hub import hf_hub_download

        models = [
            ("hpcai-tech/Open-Sora-v2", "Open_Sora_v2.safetensors", "Main model"),
            ("hpcai-tech/Open-Sora-v2", "hunyuan_vae.safetensors", "VAE"),
        ]

        for repo, filename, name in models:
            try:
                print(f"\n{name}: {repo}/{filename}")
                path = hf_hub_download(repo, filename)
                print(f"  ✓ Available: {path}")
            except Exception as e:
                print(f"  ✗ Error: {e}")

    except ImportError:
        print("  ⚠ huggingface_hub not installed, skipping verification")


def main():
    print("=" * 70)
    print("Open-Sora Component Config Patcher")
    print("=" * 70)
    print()
    print("This script fixes component paths to avoid state_dict errors:")
    print("  - VAE: hunyuan_vae.safetensors")
    print("  - T5: google/t5-v1_1-xxl")
    print("  - CLIP: openai/clip-vit-large-patch14")
    print("  - Model: Open_Sora_v2.safetensors")
    print()

    # Find config directory
    config_dir = find_config_dir()

    if not config_dir:
        print("ERROR: Could not find Open-Sora configs directory!")
        print()
        print("Please set OPENSORA_PATH environment variable:")
        print("  export OPENSORA_PATH=/path/to/Open-Sora")
        print()
        sys.exit(1)

    print(f"Config directory: {config_dir}")

    # Patch target files
    targets = [
        config_dir / "256px.py",
        config_dir / "768px.py",
    ]

    patched_count = 0
    for target in targets:
        if patch_config_file(target):
            patched_count += 1

    print("\n" + "=" * 70)
    if patched_count > 0:
        print(f"✓ Successfully patched {patched_count} config file(s)")
        print()
        print("Next steps:")
        print("  1. Restart GPU service:")
        print("     ./lambda_run_gpu_service.sh --api-key YOUR_KEY")
        print()
        print("  2. Or if using restart script:")
        print("     ./restart.sh --gpu-service --api-key YOUR_KEY")
        print()
        print("  3. Try generating a video")
    else:
        print("No changes needed - configs already correct")

    # Optional verification
    if '--verify' in sys.argv:
        verify_hf_downloads()

    print("=" * 70)


if __name__ == "__main__":
    main()
