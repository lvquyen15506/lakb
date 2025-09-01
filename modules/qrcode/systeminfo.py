"""
System information image generator
"""
import os
import platform
import psutil
import random
import logging
from datetime import datetime
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

# Configure logging
logger = logging.getLogger(__name__)

class ImageGenerator:
    def __init__(self):
        self.size = (1200, 800)
        self.padding = 50
        self.image = None
        self.draw = None
        self.bg_color = (0, 0, 0, 220)
        
        # Box dimensions
        self.box_x1 = self.padding
        self.box_y1 = self.padding
        self.box_x2 = self.size[0] - self.padding
        self.box_y2 = self.size[1] - self.padding
        
        # Initialize font
        self.load_fonts()
        
    def load_fonts(self):
        """Load fonts with fallbacks."""
        try:
            font_paths = ['arial.ttf', 'Arial.ttf', 'font/arial.ttf']
            font_path = None
            
            for path in font_paths:
                if os.path.exists(path):
                    font_path = path
                    break
            
            if not font_path:
                raise ValueError("No suitable font found")
                
            # Load fonts in different sizes
            self.font_large = ImageFont.truetype(font_path, 55)
            self.font_normal = ImageFont.truetype(font_path, 35)
            self.font_small = ImageFont.truetype(font_path, 25)
            
        except Exception as e:
            logger.error(f"Error loading fonts: {e}")
            raise
            
    def create_base_image(self):
        """Create the base image."""
        try:
            self.image = Image.new('RGBA', self.size, (0, 0, 0, 0))
            self.draw = ImageDraw.Draw(self.image)
            
            # Draw semi-transparent background box
            self.draw.rounded_rectangle(
                [(self.box_x1, self.box_y1), (self.box_x2, self.box_y2)],
                radius=20,
                fill=self.bg_color
            )
        except Exception as e:
            logger.error(f"Error creating base image: {e}")
            raise
            
    def draw_text_with_shadow(self, pos: Tuple[int, int], text: str, font: ImageFont.ImageFont, color: Tuple[int, int, int]):
        """Draw text with shadow effect."""
        try:
            shadow_color = (max(0, c - 50) for c in color[:3])
            shadow_pos = (pos[0] + 2, pos[1] + 2)
            
            # Draw shadow then text
            self.draw.text(shadow_pos, text, font=font, fill=(*shadow_color, 255))
            self.draw.text(pos, text, font=font, fill=(*color, 255))
        except Exception as e:
            logger.error(f"Error drawing text: {e}")
            
    def get_random_color(self):
        """Generate a random bright color."""
        return (random.randint(150, 255), random.randint(150, 255), random.randint(150, 255))
        
    def get_system_info(self):
        """Collect system information."""
        try:
            info = {
                "OS": f"{platform.system()} {platform.release()}",
                "CPU": platform.processor(),
                "Memory": f"Total: {psutil.virtual_memory().total / (1024**3):.1f} GB",
                "Python": platform.python_version()
            }
            return info
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {"Error": "Could not retrieve system information"}
            
    def create_info_image(self):
        """Create the full system information image."""
        try:
            self.create_base_image()
            
            # Draw title
            title = "System Information"
            title_color = self.get_random_color()
            title_pos = (self.box_x1 + 30, self.box_y1 + 30)
            self.draw_text_with_shadow(title_pos, title, self.font_large, title_color)
            
            # Draw timestamp
            time_text = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
            time_color = self.get_random_color()
            time_pos = (self.box_x2 - 250, self.box_y1 + 30)
            self.draw_text_with_shadow(time_pos, time_text, self.font_small, time_color)
            
            # Draw system info
            info = self.get_system_info()
            start_y = self.box_y1 + 120
            start_x = self.box_x1 + 50
            
            for i, (key, value) in enumerate(info.items()):
                y_pos = start_y + i * 60
                label_color = self.get_random_color()
                value_color = self.get_random_color()
                
                # Draw label
                self.draw_text_with_shadow(
                    (start_x, y_pos),
                    f"{key}:",
                    self.font_normal,
                    label_color
                )
                
                # Draw value
                self.draw_text_with_shadow(
                    (start_x + 180, y_pos),
                    str(value),
                    self.font_normal,
                    value_color
                )
                
            # Save image
            self.image.save("info.png", "PNG")
            return "info.png"
            
        except Exception as e:
            logger.error(f"Error creating info image: {e}")
            raise
