#!/usr/bin/env python3

# set up logging
import os, logging.config
logging.config.fileConfig(os.path.join(os.path.dirname(__file__), 'config', 'logging.conf'))

# suppress warnings that might come from hardware libraries
import warnings
warnings.filterwarnings("ignore", message=".*Busy Wait: Held high.*")

import os
import random
import time
import sys
import json
import logging
import threading
from utils.app_utils import generate_startup_image
from flask import Flask, request
from werkzeug.serving import is_running_from_reloader
from config import Config
from display.display_manager import DisplayManager
from refresh_task import RefreshTask
from blueprints.main import main_bp
from blueprints.settings import settings_bp
from blueprints.plugin import plugin_bp
from blueprints.playlist import playlist_bp
from jinja2 import ChoiceLoader, FileSystemLoader
from plugins.plugin_registry import load_plugins


logger = logging.getLogger(__name__)

logger.info("Starting InkyPi local development server")
app = Flask(__name__)
template_dirs = [
   os.path.join(os.path.dirname(__file__), "templates"),    # Default template folder
   os.path.join(os.path.dirname(__file__), "plugins"),      # Plugin templates
]
app.jinja_loader = ChoiceLoader([FileSystemLoader(directory) for directory in template_dirs])

device_config = Config()
display_manager = DisplayManager(device_config)
refresh_task = RefreshTask(device_config, display_manager, app)

load_plugins(device_config.get_plugins())

# Store dependencies
app.config['DEVICE_CONFIG'] = device_config
app.config['DISPLAY_MANAGER'] = display_manager
app.config['REFRESH_TASK'] = refresh_task

# Set local development flag in Flask config
app.config['INKYPI_LOCAL_DEV'] = True

# Register Blueprints
app.register_blueprint(main_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(plugin_bp)
app.register_blueprint(playlist_bp)

if __name__ == '__main__':
    from werkzeug.serving import is_running_from_reloader

    print("=" * 60)
    print("InkyPi Local Development Server")
    print("=" * 60)
    print(f"Display Type: {device_config.get_config('display_type')}")
    print(f"Resolution: {device_config.get_resolution()}")
    print(f"Images will be saved to: {device_config.current_image_file}")
    print(f"Timestamped outputs in: {os.path.join(os.path.dirname(device_config.current_image_file), 'local_outputs')}")
    print("=" * 60)

    # start the background refresh task - always start it for local development
    refresh_task.start()

    # display default inkypi image on startup
    if device_config.get_config("startup") is True:
        logger.info("Startup flag is set, displaying startup image")
        img = generate_startup_image(device_config.get_resolution())
        display_manager.display_image(img)
        device_config.update_value("startup", False, write=True)

    try:
        # Run the Flask app on localhost port 8080 for development (avoiding port 5000 conflict with macOS)
        app.secret_key = str(random.randint(100000,999999))
        print(f"\nStarting server at http://localhost:8080")
        print("Press Ctrl+C to stop")
        app.run(host="127.0.0.1", port=8080, debug=True)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        refresh_task.stop()
