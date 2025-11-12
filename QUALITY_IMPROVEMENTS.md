# 🎨 Video Quality Improvement Guide

## Current Quality Settings

Your system is configured for **production-quality videos** with:
- **Resolution**: ✅ **768px** (production quality, matches showcase)
- **Quality Steps**: 120 (diffusion steps)
- **Prompt Strength**: 12.0 (text guidance)
- **Image Influence**: 3.5 (face preservation)
- **GPU**: Fully utilized (no offloading)
- **VAE Tiling**: Disabled (prevents artifacts)

**Default configuration delivers showcase-quality results!** 🎉

---

## 🚀 Further Quality Improvements

### 1. **Increase to MAXIMUM Quality Settings**

Edit your `.env` file to use absolute maximum values:

```bash
# Maximum quality (slower but best results)
DEFAULT_NUM_STEPS=150        # Was 120, increase to maximum
DEFAULT_GUIDANCE=15.0        # Was 12.0, stronger prompt adherence
DEFAULT_GUIDANCE_IMG=4.5     # Was 3.5, even stronger face preservation
```

**Impact**:
- 25% longer generation time
- Significantly better detail and coherence
- Stronger prompt following

---

### 3. **Optimize Prompts for Best Results**

**Prompt Engineering Best Practices:**

✅ **DO:**
- Be specific and detailed: "A young woman with long brown hair, wearing a red dress, smiling at the camera"
- Include lighting: "soft natural lighting", "golden hour", "studio lighting"
- Specify style: "photorealistic", "cinematic", "professional photography"
- Mention camera work: "close-up", "medium shot", "slow pan"
- Add mood: "cheerful", "dramatic", "peaceful"

❌ **DON'T:**
- Use vague terms: "a person"
- Leave out important details
- Use conflicting descriptors
- Make prompts too long (>200 words)

**Example Good Prompts:**
```
"A professional headshot of a middle-aged businessman in a dark suit,
confident expression, office background with soft bokeh, natural window
lighting from the left, photorealistic, high detail, 4K quality"

"Close-up of a young girl laughing, curly blonde hair, bright blue eyes,
outdoor setting with green park background, golden hour lighting, shallow
depth of field, cinematic look"

"Slow motion footage of ocean waves crashing on rocks, dramatic cloudy sky,
sunset colors, aerial perspective, 4K cinematic quality"
```

---

### 4. **Use High-Quality Reference Images**

When using image-to-video:

✅ **Best practices:**
- Use high-resolution images (1920x1080 or higher)
- Ensure good lighting in reference image
- Clear, sharp focus on subject
- Proper exposure (not too dark/bright)
- Minimal compression artifacts

**Upscale your images first:**
```bash
# Use AI upscaling tools
- Real-ESRGAN
- Waifu2x (for anime/illustrated content)
- Topaz Gigapixel AI
```

---

### 5. **Adjust Generation Parameters Per Request**

You can override defaults in API requests:

```bash
curl -X POST "http://your-gpu:8001/api/generate" \
  -F "prompt=Your detailed prompt here" \
  -F "num_steps=150" \
  -F "cfg_scale=15.0" \
  -F "duration=3" \
  -F "aspect_ratio=16:9"
```

**Quality vs Speed Tradeoff:**

| Profile | num_steps | guidance | Time | Quality |
|---------|-----------|----------|------|---------|
| **Fast** | 50 | 7.0 | 1x | Good |
| **Balanced** | 100 | 10.0 | 2x | Great |
| **High** | 120 | 12.0 | 2.5x | Excellent |
| **Maximum** | 150 | 15.0 | 3x | Best |
| **Ultra** | 200 | 18.0 | 4x | Outstanding |
| **Extreme** | 250 | 19.5 | 5x | Near Perfect |
| **INSANE** | 300 | 20.0 | 6x | Absolute Best |

---

### 6. **Post-Processing Improvements**

After generation, enhance quality with:

**A. Video Upscaling:**
- Use **Topaz Video AI** for 2x or 4x upscaling
- Use **Real-ESRGAN Video** for free upscaling
- Use **DAIN** or **RIFE** for frame interpolation (increase FPS)

**B. Enhancement:**
- Color grading (DaVinci Resolve)
- Denoising (if needed)
- Sharpening (subtle)
- Stabilization

---

### 7. **Model Checkpoint Upgrades**

Use higher quality checkpoints if available:

```bash
# Edit .env file
CHECKPOINT_PATH=hpcai-tech/OpenSora-STDiT-v3-XL/model.safetensors
```

**Check available models:**
- OpenSora-STDiT-v3 (current)
- OpenSora-STDiT-v3-XL (larger, better quality)
- Custom fine-tuned models

---

### 8. **Increase Frame Count for Smoother Motion**

Currently using 8 FPS. For smoother videos:

**Option A: Generate at higher FPS**
```bash
# Edit gpu_service/config.py
FRAMES_PER_SECOND = 16  # Smoother motion
```

**Option B: Post-process with frame interpolation**
```bash
# Use RIFE or DAIN to interpolate to 24/30/60 FPS
```

---

## 🎯 Recommended Quality Upgrade Path

**Good news:** Fresh installations already use 768px by default! ✅

### Step 1: Maximize Quality Settings (5 minutes)
```bash
# Option A: Use the automated script (recommended)
cd ~/sora2
./enable_max_quality.sh

# Option B: Manual edit of .env file
# Edit ~/sora2/.env and add:
DEFAULT_NUM_STEPS=150
DEFAULT_GUIDANCE=15.0
DEFAULT_GUIDANCE_IMG=4.5

# IMPORTANT: Restart service for changes to take effect
sudo systemctl restart opensora-gpu
```

### Step 2: Improve Prompts (immediate)
- Use detailed, specific descriptions
- Include lighting and style
- Add camera work descriptions

### Step 3: Post-Processing (optional)
- Upscale with Topaz or Real-ESRGAN
- Color grade for final polish

---

## 📊 Quality Comparison

### Current (Default Settings)
- ✅ **768px resolution** (production quality)
- 120 steps, 12.0 guidance, 3.5 image guidance
- Excellent quality, matches showcase videos

### Maximum Settings (Optional Upgrade)
- ✅ **768px resolution** (same)
- 150 steps, 15.0 guidance, 4.5 image guidance
- Best possible quality, slower generation

**Estimated Improvement (Default to Maximum):**
- **Detail**: +25%
- **Prompt Adherence**: +20%
- **Face Quality**: +30%
- **Overall Quality**: +25-30%

---

## ⚠️ Important Notes

1. **VRAM Requirements:**
   - ✅ **768px (default)**: ~24-32GB VRAM (A100/H100 recommended)
   - 256px (testing only): ~16GB VRAM

2. **Generation Time:**
   - Default 768px: ~3-4 minutes per video
   - Maximum quality (150 steps): ~4-5 minutes per video
   - Ultra/Extreme/Insane: 5-12 minutes per video

3. **Diminishing Returns:**
   - Above 150 steps, improvements become minimal
   - Default 768px already delivers showcase-quality results
   - Focus on prompts and proper settings for best ROI

---

## 🔧 Quick Quality Boost Script

```bash
#!/bin/bash
# Apply maximum quality settings

cd ~/sora2

# Update .env with maximum settings
cat >> .env << 'EOF'

# MAXIMUM QUALITY SETTINGS
DEFAULT_NUM_STEPS=150
DEFAULT_GUIDANCE=15.0
DEFAULT_GUIDANCE_IMG=4.5
EOF

# Restart service
sudo systemctl restart opensora-gpu

echo "✅ Maximum quality settings applied!"
echo "Generation will be slower but much higher quality"
```

Save as `enable_max_quality.sh` and run: `bash enable_max_quality.sh`

---

## 💡 Pro Tips

1. **Test before production**: Generate short videos (2s) to test settings
2. **Balance quality vs time**: Use fast settings for previews, max for finals
3. **Batch processing**: Generate multiple variations with different seeds
4. **Reference images matter**: Spend time on high-quality reference images
5. **Iterate on prompts**: Small prompt changes can make big differences

---

Need help with specific quality issues? Check the troubleshooting section or provide sample outputs for analysis.
