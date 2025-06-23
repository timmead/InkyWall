import logging
import os
from display.abstract_display import AbstractDisplay

logger = logging.getLogger(__name__)

class LocalDisplay(AbstractDisplay):
    """
    Local development display driver that saves images instead of driving hardware.

    This class is used for local development when running without Raspberry Pi hardware.
    Instead of sending images to a physical display, it saves them to the file system.
    """

    def initialize_display(self):
        """
        Initializes the local display.

        Sets a default resolution and ensures the output directory exists.
        """

        logger.info("Initializing local display for development")

        # Set default resolution if not already configured
        if not self.device_config.get_config("resolution"):
            # Default to a common e-ink display resolution
            self.device_config.update_value(
                "resolution",
                [800, 480],
                write=True)

        # Ensure output directory exists
        os.makedirs(os.path.dirname(self.device_config.current_image_file), exist_ok=True)

        logger.info(f"Local display initialized with resolution: {self.device_config.get_resolution()}")

    def display_image(self, image, image_settings=[]):
        """
        Saves the provided image to the file system instead of displaying on hardware.

        Args:
            image (PIL.Image): The image to be saved.
            image_settings (list, optional): Additional settings (unused in local mode).
        """

        logger.info("Saving image for local display")
        if not image:
            raise ValueError("No image provided.")

        # Save the image to the current image file location
        image.save(self.device_config.current_image_file)
        logger.info(f"Image saved to: {self.device_config.current_image_file}")

        # Optionally save with timestamp for development tracking
        timestamp_filename = f"display_output_{int(__import__('time').time())}.png"
        timestamp_path = os.path.join(
            os.path.dirname(self.device_config.current_image_file),
            "local_outputs",
            timestamp_filename
        )

        os.makedirs(os.path.dirname(timestamp_path), exist_ok=True)
        image.save(timestamp_path)
        logger.info(f"Timestamped image saved to: {timestamp_path}")
