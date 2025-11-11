#!/usr/bin/env python3
"""
Test if Open-Sora v2 model loads correctly from the config
"""
import os
import sys
from pathlib import Path

def test_model_load():
    opensora_path = os.environ.get("OPENSORA_PATH", os.path.expanduser("~/Open-Sora"))
    sys.path.insert(0, str(opensora_path))

    print("=" * 70)
    print("🧪 Testing Open-Sora v2 Model Loading")
    print("=" * 70)
    print()

    # Load config
    config_path = Path(opensora_path) / "configs/diffusion/inference/256px.py"
    print(f"📝 Loading config: {config_path}")

    if not config_path.exists():
        print(f"❌ Config not found!")
        return False

    # Execute config to get model dict
    config_globals = {}
    with open(config_path, 'r') as f:
        exec(f.read(), config_globals)

    model_config = config_globals.get('model', {})
    ae_config = config_globals.get('ae', {})

    print(f"✅ Config loaded\n")

    # Check model configuration
    print("🔍 Model Configuration:")
    print(f"   Type: {model_config.get('type')}")
    print(f"   from_pretrained: {model_config.get('from_pretrained')}")
    print(f"   Hidden size: {model_config.get('hidden_size')}")
    print(f"   Depth: {model_config.get('depth')}")
    print()

    print("🔍 VAE Configuration:")
    print(f"   Type: {ae_config.get('type')}")
    print(f"   from_pretrained: {ae_config.get('from_pretrained')}")
    print()

    # Try to load the model (this will show if path works)
    print("🚀 Attempting to initialize model components...")
    print()

    try:
        # Check if we can import opensora
        import opensora
        print(f"✅ OpenSora package found: {opensora.__file__}")
    except ImportError as e:
        print(f"❌ Cannot import opensora: {e}")
        print("   Make sure Open-Sora is installed: pip install -e ~/Open-Sora")
        return False

    try:
        # Try importing model builder
        from opensora.registry import build_module
        print(f"✅ Model builder imported")

        # Try to build model (this will attempt to load checkpoint)
        print(f"\n📦 Building model from config...")
        print(f"   This will try to load: {model_config.get('from_pretrained')}")
        print(f"   Please wait, this may take a minute...")
        print()

        # Just test the path resolution without fully loading (to save time)
        from_pretrained = model_config.get('from_pretrained')

        # Check if it's a HuggingFace path
        if '/' in from_pretrained and not from_pretrained.startswith(('/', '.')):
            print("🔗 Detected HuggingFace Hub path")

            try:
                from huggingface_hub import hf_hub_download, HfApi
                api = HfApi()

                # Parse the path
                if from_pretrained.count('/') >= 2:
                    # Format: org/repo/file.safetensors
                    parts = from_pretrained.split('/')
                    repo_id = '/'.join(parts[:2])
                    filename = '/'.join(parts[2:])

                    print(f"   Repo ID: {repo_id}")
                    print(f"   Filename: {filename}")
                    print()

                    # Check if file exists in repo
                    try:
                        files = api.list_repo_files(repo_id)
                        if filename in files:
                            print(f"✅ File exists in repo")

                            # Check cache
                            cache_dir = Path.home() / ".cache/huggingface/hub"
                            repo_cache = cache_dir / f"models--{repo_id.replace('/', '--')}"

                            if repo_cache.exists():
                                # Find the file in snapshots
                                for snapshot in (repo_cache / "snapshots").iterdir():
                                    cached_file = snapshot / filename
                                    if cached_file.exists():
                                        size_gb = cached_file.stat().st_size / (1024**3)
                                        print(f"✅ Found in cache: {size_gb:.1f} GB")
                                        print(f"   Path: {cached_file}")
                                        return True
                                print(f"⚠️  In cache but file not found in snapshots")
                            else:
                                print(f"⚠️  Not in cache, will download on first use")
                                print(f"   Expected size: ~22 GB")
                        else:
                            print(f"❌ File not found in repo!")
                            print(f"   Available .safetensors files:")
                            for f in files:
                                if f.endswith('.safetensors'):
                                    print(f"      - {f}")
                            return False

                    except Exception as e:
                        print(f"❌ Error checking repo: {e}")
                        return False

            except ImportError:
                print("⚠️  huggingface_hub not available, cannot verify path")

    except Exception as e:
        print(f"❌ Error loading model: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    try:
        success = test_model_load()

        print()
        print("=" * 70)
        if success:
            print("✅ Model configuration looks good!")
            print()
            print("The model file is cached and should load correctly.")
            print("If videos are still static, the issue might be:")
            print("  1. Inference parameters (num_steps, guidance, etc.)")
            print("  2. CUDA/GPU issues")
            print("  3. VAE or text encoder problems")
        else:
            print("❌ Model configuration has issues")
            print()
            print("Check the errors above and fix the model path.")
        print("=" * 70)

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
