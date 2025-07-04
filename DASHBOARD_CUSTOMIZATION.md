# Dashboard Background Customization

The SBOM Platform dashboard now features a NATO AWACS themed background. This document explains how to customize the background image.

## Current Implementation

The dashboard includes:
- **Transparent NATO AWACS SVG** in the main background
- **Smaller AWACS image** in the header area
- **NATO-themed branding** with military-grade messaging
- **Glass-morphism cards** with transparency effects

## How to Replace the NATO AWACS Image

### Option 1: Replace the SVG File

1. **Create your own transparent image** (PNG, SVG, or any web format)
2. **Replace the existing file:**
   ```bash
   # Replace with your image
   cp /path/to/your/image.png src/static/images/nato-awacs.svg
   # OR for different format, update the CSS references
   ```

3. **Rebuild the container:**
   ```bash
   docker-compose -f docker-compose-simple.yml build --no-cache
   docker-compose -f docker-compose-simple.yml up -d
   ```

### Option 2: Use a Different Image Format

1. **Add your image to the static directory:**
   ```bash
   cp /path/to/your/background.png src/static/images/
   ```

2. **Update the CSS in `src/monitoring/dashboard.py`:**
   ```python
   # Change line ~45 from:
   background-image: url('/static/images/nato-awacs.svg');
   # To:
   background-image: url('/static/images/your-background.png');
   
   # Also update line ~68 for the header:
   background-image: url('/static/images/your-background.png');
   ```

### Option 3: Use an External Image URL

Update the CSS to use an external image:
```python
background-image: url('https://example.com/your-image.png');
```

## Background Properties Explained

### Main Background (Body)
```css
background-image: url('/static/images/nato-awacs.svg');
background-repeat: no-repeat;          # Don't repeat the image
background-position: center center;    # Center the image
background-attachment: fixed;          # Fixed during scrolling
background-size: 800px 400px;         # Size of the background
```

### Header Background
```css
background-image: url('/static/images/nato-awacs.svg');
background-repeat: no-repeat;
background-position: right center;     # Position in header
background-size: 200px 100px;         # Smaller size for header
opacity: 0.15;                        # Very transparent
```

## Customization Tips

### For Transparency Effects:
- Use **PNG with transparency** or **SVG** formats
- Adjust **opacity** values in CSS (0.1 = very transparent, 1.0 = opaque)
- Consider the **backdrop-filter: blur()** effect on cards

### For Different Organizations:
- Replace NATO branding in the header text
- Update the title from "NATO-Grade" to your organization
- Modify the AWACS subtitle to match your theme

### Background Size Guidelines:
- **Main background**: 800x400px works well for most screens
- **Header background**: 200x100px for the header area
- Use **vector formats (SVG)** for scalability

## File Locations

- **Static files**: `src/static/images/`
- **Dashboard CSS**: `src/monitoring/dashboard.py` (lines 40-80)
- **Container build**: Updates require container rebuild

## Example Customizations

### Corporate Theme:
```css
background-image: url('/static/images/company-logo.svg');
background-size: 600px 300px;
opacity: 0.05;
```

### Military/Defense Theme:
```css
background-image: url('/static/images/radar-sweep.svg');
background-size: 1000px 500px;
background-position: center center;
```

### Minimal Theme:
```css
/* Remove background image entirely */
background-image: none;
background: linear-gradient(45deg, #f5f5f5 0%, #e8e8e8 100%);
```

## Testing Your Changes

1. **Local development:**
   ```bash
   python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8080
   ```

2. **Container deployment:**
   ```bash
   docker-compose -f docker-compose-simple.yml build --no-cache
   docker-compose -f docker-compose-simple.yml up -d
   ```

3. **Verify the image loads:**
   ```bash
   curl http://localhost:8080/static/images/your-image.png
   ```

4. **Check the dashboard:**
   Open `http://localhost:8080/dashboard` in your browser

## Current NATO AWACS Features

The included NATO AWACS SVG features:
- **Animated radar sweep** (rotating line)
- **Aircraft silhouette** with transparent colors
- **NATO star symbol**
- **Radar dome visualization**
- **Blue color scheme** matching the dashboard

This creates a professional, military-grade appearance suitable for defense and security applications.