import requests
from PIL import Image, ImageEnhance
from io import BytesIO
import os
import logging
import hashlib
import tempfile
import subprocess
import sys

logger = logging.getLogger(__name__)

def get_image(image_url):
    response = requests.get(image_url)
    img = None
    if 200 <= response.status_code < 300 or response.status_code == 304:
        img = Image.open(BytesIO(response.content))
    else:
        logger.error(f"Received non-200 response from {image_url}: status_code: {response.status_code}")
    return img

def change_orientation(image, orientation, inverted=False):
    if orientation == 'horizontal':
        angle = 0
    elif orientation == 'vertical':
        angle = 90

    if inverted:
        angle = (angle + 180) % 360

    return image.rotate(angle, expand=1)

def resize_image(image, desired_size, image_settings=[]):
    img_width, img_height = image.size
    desired_width, desired_height = desired_size
    desired_width, desired_height = int(desired_width), int(desired_height)

    img_ratio = img_width / img_height
    desired_ratio = desired_width / desired_height

    keep_width = "keep-width" in image_settings

    x_offset, y_offset = 0,0
    new_width, new_height = img_width,img_height
    # Step 1: Determine crop dimensions
    desired_ratio = desired_width / desired_height
    if img_ratio > desired_ratio:
        # Image is wider than desired aspect ratio
        new_width = int(img_height * desired_ratio)
        if not keep_width:
            x_offset = (img_width - new_width) // 2
    else:
        # Image is taller than desired aspect ratio
        new_height = int(img_width / desired_ratio)
        if not keep_width:
            y_offset = (img_height - new_height) // 2

    # Step 2: Crop the image
    cropped_image = image.crop((x_offset, y_offset, x_offset + new_width, y_offset + new_height))

    # Step 3: Resize to the exact desired dimensions (if necessary)
    return cropped_image.resize((desired_width, desired_height), Image.LANCZOS)

def apply_image_enhancement(img, image_settings={}):

    # Apply Brightness
    img = ImageEnhance.Brightness(img).enhance(image_settings.get("brigtness", 1.0))

    # Apply Contrast
    img = ImageEnhance.Contrast(img).enhance(image_settings.get("contrast", 1.0))

    # Apply Saturation (Color)
    img = ImageEnhance.Color(img).enhance(image_settings.get("saturation", 1.0))

    # Apply Sharpness
    img = ImageEnhance.Sharpness(img).enhance(image_settings.get("sharpness", 1.0))

    return img

def compute_image_hash(image):
    """Compute SHA-256 hash of an image."""
    image = image.convert("RGB")
    img_bytes = image.tobytes()
    return hashlib.sha256(img_bytes).hexdigest()

def take_screenshot_html(html_str, dimensions, timeout_ms=None):
    image = None
    try:
        # Check if we're in local development mode from Flask app config
        is_local_dev = False
        try:
            from flask import current_app
            is_local_dev = current_app.config.get('INKYWALL_LOCAL_DEV', False)
        except RuntimeError:
            # We're outside of Flask application context, default to production mode
            is_local_dev = False

        final_html = html_str

        # Only add debug container if we're in local dev mode and debug browser is enabled
        if is_local_dev:
            # Parse the existing HTML to add debug styling
            if '<html>' in html_str.lower():
                # HTML already has structure, just inject debug styles
                head_end = html_str.lower().find('</head>')
                if head_end != -1:
                    debug_styles = f"""
                    <style>
                        /* Debug Browser Constraints */
                        html, body {{
                            margin: 0 !important;
                            padding: 0 !important;
                            width: {dimensions[0]}px !important;
                            height: {dimensions[1]}px !important;
                            overflow: hidden !important;
                            box-sizing: border-box !important;
                        }}
                        body {{
                            border: 3px solid #ff4444 !important;
                            position: relative !important;
                        }}
                        body::before {{
                            content: "🔍 DEBUG: {dimensions[0]}×{dimensions[1]} Screenshot Area" !important;
                            position: absolute !important;
                            top: 0 !important;
                            left: 0 !important;
                            right: 0 !important;
                            background: rgba(255, 68, 68, 0.9) !important;
                            color: white !important;
                            padding: 4px 8px !important;
                            font-size: 11px !important;
                            font-family: -apple-system, BlinkMacSystemFont, monospace !important;
                            font-weight: bold !important;
                            z-index: 999999 !important;
                            pointer-events: none !important;
                            text-align: center !important;
                        }}
                    </style>"""
                    final_html = html_str[:head_end] + debug_styles + html_str[head_end:]

        # Create a temporary HTML file
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as html_file:
            html_file.write(final_html.encode("utf-8"))
            html_file_path = html_file.name

        image = take_screenshot(html_file_path, dimensions, timeout_ms)

        # Remove html file
        os.remove(html_file_path)

    except Exception as e:
        logger.error(f"Failed to take screenshot: {str(e)}")

    return image

def take_screenshot(target, dimensions, timeout_ms=None):
    image = None
    try:
        # Create a temporary output file for the screenshot
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as img_file:
            img_file_path = img_file.name

        # Check for different Chrome/Chromium installations
        # Prioritize chromium-headless-shell for production (Raspberry Pi)
        # Fall back to other Chrome installations for local development

        # Check if we're in local development mode from Flask app config
        is_local_dev = False
        try:
            from flask import current_app
            is_local_dev = current_app.config.get('INKYWALL_LOCAL_DEV', False)
        except RuntimeError:
            # We're outside of Flask application context, default to production mode
            is_local_dev = False

        if is_local_dev:
            # Local development paths (macOS first, then Linux alternatives)
            chrome_paths = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # macOS Chrome
                "google-chrome-stable",  # Linux alternative
                "chromium",  # Linux alternative
                "google-chrome",  # Linux alternative
                "chromium-headless-shell",  # Original (try last for local dev)
            ]
        else:
            # Production paths (Raspberry Pi / Linux)
            chrome_paths = [
                "chromium-headless-shell",  # R-Pi default
            ]

        chrome_cmd = None
        for path in chrome_paths:
            try:
                # For absolute paths, just check if file exists
                if os.path.isabs(path):
                    if os.path.exists(path):
                        chrome_cmd = path
                        break
                # For relative paths/commands, use 'which' to check if available in PATH
                else:
                    if subprocess.run(["which", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
                        chrome_cmd = path
                        break
            except:
                continue

        if not chrome_cmd:
            logger.error("No Chrome/Chromium browser found for screenshots")
            return None

        if is_local_dev:
            # Create a temporary user data directory for isolated Chrome instance
            with tempfile.TemporaryDirectory() as temp_user_data_dir:
                # Build the base command - use native ARM on macOS for better performance
                if sys.platform == "darwin" and chrome_cmd == "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome":
                    # Force native ARM execution on macOS to avoid Rosetta performance issues
                    base_command = ["arch", "-arm64", chrome_cmd, target]
                else:
                    base_command = [chrome_cmd, target]

                command = base_command + [
                    f"--screenshot={img_file_path}", f'--window-size={dimensions[0]},{dimensions[1]}',
                    "--headless", "--no-sandbox"
                ]

                if timeout_ms:
                    command.append(f"--timeout={timeout_ms}")

                try:
                    logger.info(f"Opening debug browser window for: {target}")
                    # Create debug browser command with native ARM on macOS
                    if sys.platform == "darwin" and chrome_cmd == "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome":
                        debug_base_command = ["arch", "-arm64", chrome_cmd, target]
                    else:
                        debug_base_command = [chrome_cmd, target]

                    debug_command = debug_base_command + [
                        f'--window-size={dimensions[0]},{dimensions[1]}',
                        "--no-sandbox", "--disable-web-security", "--disable-features=VizDisplayCompositor",
                        "--new-window"
                    ]

                    # Launch debug browser in background
                    subprocess.Popen(debug_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    logger.info("Debug browser opened")

                except Exception as e:
                    logger.warning(f"Failed to open debug browser (continuing with screenshot): {str(e)}")
        else:
            command = [
                chrome_cmd, target, "--headless",
                f"--screenshot={img_file_path}", f'--window-size={dimensions[0]},{dimensions[1]}',
                "--no-sandbox", "--disable-gpu", "--disable-software-rasterizer",
                "--disable-dev-shm-usage", "--hide-scrollbars", "--force-device-scale-factor=1"
        ]

        if timeout_ms:
            command.append(f"--timeout={timeout_ms}")

        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Log the command output for debugging
        if result.stdout:
            logger.debug(f"Chrome stdout: {result.stdout.decode('utf-8')}")
        if result.stderr:
            logger.debug(f"Chrome stderr: {result.stderr.decode('utf-8')}")

        # Check if the process failed or the output file is missing
        if result.returncode != 0:
            logger.error(f"Chrome process failed with return code: {result.returncode}")
            logger.error(f"Chrome stderr: {result.stderr.decode('utf-8')}")
            return None

        if not os.path.exists(img_file_path):
            logger.error(f"Screenshot file not created: {img_file_path}")
            return None

        # Check if the file has content
        file_size = os.path.getsize(img_file_path)
        logger.info(f"Screenshot file created: {img_file_path} (size: {file_size} bytes)")

        # Load the image using PIL
        image = Image.open(img_file_path)
        logger.info(f"Screenshot loaded successfully: {image.size}")

        # Remove image files
        os.remove(img_file_path)

    except Exception as e:
        logger.error(f"Failed to take screenshot: {str(e)}")

    return image
