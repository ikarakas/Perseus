# How to Add Your Real NATO AWACS Image

The dashboard is now configured to use a real NATO AWACS photograph as the background. Follow these steps to add your image:

## Step 1: Save Your AWACS Image

Save your NATO AWACS aircraft photo to:
```
src/static/images/nato-awacs-real.jpg
```

**Image Requirements:**
- **Format**: JPG, PNG, or WebP
- **Size**: High resolution recommended (the CSS will scale it)
- **Content**: The beautiful NATO AWACS aircraft you showed
- **Filename**: Must be exactly `nato-awacs-real.jpg`

## Step 2: Rebuild the Container

After adding your image:

```bash
# Rebuild with your real AWACS image
docker-compose -f docker-compose-simple.yml build --no-cache
docker-compose -f docker-compose-simple.yml up -d
```

## What's Changed

The dashboard CSS has been updated to:

### Main Background:
- **Image**: `nato-awacs-real.jpg` (your real AWACS photo)
- **Size**: 900x600px (larger to show detail)
- **Opacity**: 0.08 (very subtle, won't interfere with UI)
- **Position**: Center center (showcases the aircraft)

### Header Background:
- **Image**: Same real AWACS photo
- **Size**: 300x200px (smaller for header area)
- **Opacity**: 0.12 (slightly more visible in header)
- **Position**: Right center (accent in header)

## Expected Result

Your dashboard will feature:
- ✈️ **Real NATO AWACS aircraft** as a subtle background
- 🛡️ **Professional military appearance** with actual aircraft
- 🎨 **Glass-morphism cards** that work with the photo background
- 📱 **Responsive design** that scales on different screens

## Alternative: Use Different File Name

If you want to use a different filename:

1. **Save your image** as any name in `src/static/images/`
2. **Update the CSS** in `src/monitoring/dashboard.py`:
   ```python
   # Change lines 45 and 68 from:
   background-image: url('/static/images/nato-awacs-real.jpg');
   # To:
   background-image: url('/static/images/your-filename.jpg');
   ```

## Troubleshooting

**Image not showing?**
- Check the file path: `src/static/images/nato-awacs-real.jpg`
- Verify the container was rebuilt
- Test direct access: `curl http://localhost:8080/static/images/nato-awacs-real.jpg`

**Image too bright/dark?**
- Adjust opacity in CSS (lines 50 and 72)
- Lower values = more transparent
- Higher values = more visible

**Want different positioning?**
- Main background: Change `background-position: center center`
- Header background: Change `background-position: right center`

The real AWACS photo will give your dashboard an authentic, professional military appearance! 🛩️