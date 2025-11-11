#!/usr/bin/env python3
"""
Diagnose model loading issues with Open-Sora
"""
import os
import sys
from pathlib import Path

def check_huggingface_cache():
    """Check what models are cached"""
    cache_dir = Path.home() / ".cache/huggingface/hub"
    print(f"🔍 Checking HuggingFace cache: {cache_dir}\n")

    if not cache_dir.exists():
        print("❌ HuggingFace cache directory not found!")
        return

    # Look for Open-Sora models
    for repo_dir in cache_dir.glob("models--*Open*Sora*"):
        print(f"📦 Found repo: {repo_dir.name}")

        # Check snapshots
        snapshots_dir = repo_dir / "snapshots"
        if snapshots_dir.exists():
            for snapshot in snapshots_dir.iterdir():
                print(f"   📸 Snapshot: {snapshot.name}")

                # List safetensors files
                for sf_file in snapshot.rglob("*.safetensors"):
                    size_mb = sf_file.stat().st_size / (1024 * 1024)
                    print(f"      📄 {sf_file.relative_to(snapshot)} ({size_mb:.1f} MB)")
        print()

def check_opensora_config():
    """Check the current Open-Sora config"""
    opensora_path = os.environ.get("OPENSORA_PATH", os.path.expanduser("~/Open-Sora"))
    config_file = Path(opensora_path) / "configs/diffusion/inference/256px.py"

    print(f"📝 Checking config: {config_file}\n")

    if not config_file.exists():
        print("❌ Config file not found!")
        return

    with open(config_file, 'r') as f:
        content = f.read()

    # Extract from_pretrained paths
    import re
    pretrained_paths = re.findall(r'from_pretrained\s*=\s*["\']([^"\']+)["\']', content)

    print("🔗 Model paths in config:")
    for path in pretrained_paths:
        print(f"   • {path}")
    print()

def check_model_file_format():
    """Check if the model path format needs correction"""
    print("💡 Recommended formats for from_pretrained:\n")
    print("   For HuggingFace Hub files:")
    print("   ✅ 'repo/model' (downloads default model)")
    print("   ✅ 'repo' with subfolder parameter")
    print("   ⚠️  'repo/file.safetensors' (may need special handling)")
    print()
    print("   For Open-Sora-v2:")
    print("   Option 1: from_pretrained='hpcai-tech/Open-Sora-v2', filename='Open_Sora_v2.safetensors'")
    print("   Option 2: from_pretrained='hpcai-tech/Open-Sora-v2/resolve/main/Open_Sora_v2.safetensors'")
    print()

if __name__ == "__main__":
    print("=" * 70)
    print("🔧 Open-Sora Model Loading Diagnostics")
    print("=" * 70)
    print()

    check_huggingface_cache()
    check_opensora_config()
    check_model_file_format()

    print("=" * 70)
    print("✅ Diagnostic complete!")
    print("=" * 70)
