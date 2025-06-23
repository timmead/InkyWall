# InkyPi Local Development

This guide will help you run InkyPi locally for development and testing without requiring Raspberry Pi hardware.

## Quick Start

1. **Run the setup script:**

   ```bash
   python install/local_setup.py
   ```

2. **Install dependencies:**

   ```bash
   pip install -r install/requirements-local.txt
   ```

3. **Start the local development server:**

   ```bash
   python src/inkypi_local.py
   ```

4. **Open your browser:**
   Go to http://localhost:8080

## What's Different in Local Mode

- **No Hardware Required**: Instead of sending images to an e-ink display, they are saved as PNG files
- **Local Display Driver**: Uses `LocalDisplay` class that saves images to the filesystem
- **Development Server**: Runs on localhost:8080 with Flask debug mode enabled
- **Image Output**:
  - Current image: `src/static/images/current_image.png`
  - Timestamped outputs: `src/static/images/local_outputs/`

## Configuration

The local development environment uses `src/config/device.json` with:

- `display_type`: Set to "local"
- `resolution`: Default 600x448 (common e-ink display size)
- Other settings remain the same as the Pi version

## Plugin Development

All plugins work the same way in local mode. When a plugin generates content:

1. The image is processed normally
2. Instead of being sent to hardware, it's saved to the filesystem
3. You can view the generated images directly

## Useful Development Features

- **Debug Mode**: Flask runs with debug=True for automatic reloading
- **Timestamped Outputs**: Each generated image is saved with a timestamp for tracking
- **No Hardware Dependencies**: No need for GPIO, SPI, or specific display libraries

## API Keys

If you want to test plugins that require API keys (OpenAI, Weather, etc.):

1. Add your keys to the `.env` file:
   ```
   OPENAI_API_KEY=your_key_here
   WEATHER_API_KEY=your_key_here
   ```

## Viewing Generated Images

Generated images are saved to:

- **Current display image**: `src/static/images/current_image.png`
- **Historical outputs**: `src/static/images/local_outputs/display_output_[timestamp].png`

You can open these files with any image viewer to see what would appear on the e-ink display.

## Testing Different Resolutions

To test with different display resolutions, modify the `resolution` field in `src/config/device.json`:

```json
{
  "resolution": [800, 480]
}
```

Common e-ink display resolutions:

- 600x448 (4.2" displays)
- 800x480 (7.5" displays)
- 1404x1872 (13.3" displays)

## Troubleshooting

**Port already in use**: If port 8080 is busy, modify the port in `src/inkypi_local.py`:

```python
app.run(host="127.0.0.1", port=8081, debug=True)
```

**Missing directories**: Run `python install/local_setup.py` again to ensure all directories are created.

**Import errors**: Make sure you're in the project root directory when running the commands.
