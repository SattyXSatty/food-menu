# basic import 
from mcp.server.fastmcp import FastMCP, Image
from mcp.server.fastmcp.prompts import base
from mcp.types import TextContent
from mcp import types
from PIL import Image as PILImage, ImageDraw, ImageFont
import math
import sys
import subprocess
import time
import os
import platform

# instantiate an MCP server client
mcp = FastMCP("Calculator")

# DEFINE TOOLS

#addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    print("CALLED: add(a: int, b: int) -> int:")
    return int(a + b)

@mcp.tool()
def add_list(l: list) -> int:
    """Add all numbers in a list"""
    print("CALLED: add(l: list) -> int:")
    return sum(l)

# subtraction tool
@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtract two numbers"""
    print("CALLED: subtract(a: int, b: int) -> int:")
    return int(a - b)

# multiplication tool
@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    print("CALLED: multiply(a: int, b: int) -> int:")
    return int(a * b)

#  division tool
@mcp.tool() 
def divide(a: int, b: int) -> float:
    """Divide two numbers"""
    print("CALLED: divide(a: int, b: int) -> float:")
    return float(a / b)

# power tool
@mcp.tool()
def power(a: int, b: int) -> int:
    """Power of two numbers"""
    print("CALLED: power(a: int, b: int) -> int:")
    return int(a ** b)

# square root tool
@mcp.tool()
def sqrt(a: int) -> float:
    """Square root of a number"""
    print("CALLED: sqrt(a: int) -> float:")
    return float(a ** 0.5)

# cube root tool
@mcp.tool()
def cbrt(a: int) -> float:
    """Cube root of a number"""
    print("CALLED: cbrt(a: int) -> float:")
    return float(a ** (1/3))

# factorial tool
@mcp.tool()
def factorial(a: int) -> int:
    """factorial of a number"""
    print("CALLED: factorial(a: int) -> int:")
    return int(math.factorial(a))

# log tool
@mcp.tool()
def log(a: int) -> float:
    """log of a number"""
    print("CALLED: log(a: int) -> float:")
    return float(math.log(a))

# remainder tool
@mcp.tool()
def remainder(a: int, b: int) -> int:
    """remainder of two numbers divison"""
    print("CALLED: remainder(a: int, b: int) -> int:")
    return int(a % b)

# sin tool
@mcp.tool()
def sin(a: int) -> float:
    """sin of a number"""
    print("CALLED: sin(a: int) -> float:")
    return float(math.sin(a))

# cos tool
@mcp.tool()
def cos(a: int) -> float:
    """cos of a number"""
    print("CALLED: cos(a: int) -> float:")
    return float(math.cos(a))

# tan tool
@mcp.tool()
def tan(a: int) -> float:
    """tan of a number"""
    print("CALLED: tan(a: int) -> float:")
    return float(math.tan(a))

# mine tool
@mcp.tool()
def mine(a: int, b: int) -> int:
    """special mining tool"""
    print("CALLED: mine(a: int, b: int) -> int:")
    return int(a - b - b)

@mcp.tool()
def create_thumbnail(image_path: str) -> Image:
    """Create a thumbnail from an image"""
    print("CALLED: create_thumbnail(image_path: str) -> Image:")
    img = PILImage.open(image_path)
    img.thumbnail((100, 100))
    return Image(data=img.tobytes(), format="png")

@mcp.tool()
def strings_to_chars_to_int(string: str) -> list[int]:
    """Return the ASCII values of the characters in a word"""
    print("CALLED: strings_to_chars_to_int(string: str) -> list[int]:")
    return [int(ord(char)) for char in string]

@mcp.tool()
def int_list_to_exponential_sum(int_list: list) -> float:
    """Return sum of exponentials of numbers in a list"""
    print("CALLED: int_list_to_exponential_sum(int_list: list) -> float:")
    return sum(math.exp(i) for i in int_list)

@mcp.tool()
def fibonacci_numbers(n: int) -> list:
    """Return the first n Fibonacci Numbers"""
    print("CALLED: fibonacci_numbers(n: int) -> list:")
    if n <= 0:
        return []
    fib_sequence = [0, 1]
    for _ in range(2, n):
        fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])
    return fib_sequence[:n]


# Global variable to store the image path
current_image_path = None

@mcp.tool()
def open_preview_with_canvas(width: int = 800, height: int = 600) -> dict:
    """Open Preview app with a blank canvas. This opens the app visually on screen."""
    global current_image_path
    print(f"CALLED: open_preview_with_canvas(width={width}, height={height})")
    try:
        # Create a white canvas
        img = PILImage.new('RGB', (width, height), color='white')
        
        # Save to temp file
        current_image_path = '/tmp/mcp_canvas.png'
        img.save(current_image_path)
        
        # Open in Preview (this opens the app visually)
        if platform.system() == 'Darwin':  # macOS
            subprocess.run(['open', '-a', 'Preview', current_image_path])
            time.sleep(1)  # Wait for Preview to open
        
        return {
            "success": True,
            "message": f"Preview opened with canvas ({width}x{height})",
            "path": current_image_path
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Error opening Preview: {str(e)}"
        }

@mcp.tool()
def draw_rectangle_in_preview(x1: int, y1: int, x2: int, y2: int, color: str = "red") -> dict:
    """Draw a rectangle in the Preview window. Preview must be open first."""
    global current_image_path
    print(f"CALLED: draw_rectangle_in_preview({x1}, {y1}, {x2}, {y2}, {color})")
    try:
        if not current_image_path or not os.path.exists(current_image_path):
            return {
                "success": False,
                "message": "Preview not open. Please call open_preview_with_canvas first."
            }
        
        # Open the existing image
        img = PILImage.open(current_image_path)
        draw = ImageDraw.Draw(img)
        
        # Draw rectangle with thick border
        draw.rectangle([x1, y1, x2, y2], outline=color, width=5)
        
        # Save the image
        img.save(current_image_path)
        
        # Refresh Preview using AppleScript
        applescript = f'''
        tell application "Preview"
            activate
            close every window
            delay 0.5
            open POSIX file "{current_image_path}"
        end tell
        '''
        subprocess.run(['osascript', '-e', applescript])
        time.sleep(0.5)
        
        return {
            "success": True,
            "message": f"Rectangle drawn from ({x1},{y1}) to ({x2},{y2}) - visible in Preview"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Error drawing rectangle: {str(e)}"
        }

@mcp.tool()
def add_text_in_preview(text: str, x: int = 50, y: int = 50, font_size: int = 36) -> dict:
    """Add text in the Preview window at position (x, y). Preview must be open first."""
    global current_image_path
    print(f"CALLED: add_text_in_preview(text={text}, x={x}, y={y}, font_size={font_size})")
    try:
        if not current_image_path or not os.path.exists(current_image_path):
            return {
                "success": False,
                "message": "Preview not open. Please call open_preview_with_canvas first."
            }
        
        # Open the existing image
        img = PILImage.open(current_image_path)
        draw = ImageDraw.Draw(img)
        
        # Try to use a nice font
        try:
            font_paths = [
                '/System/Library/Fonts/Helvetica.ttc',
                '/System/Library/Fonts/SFNSDisplay.ttf',
                '/Library/Fonts/Arial.ttf'
            ]
            font = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, font_size)
                    break
            if not font:
                font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        # Draw text
        draw.text((x, y), text, fill='black', font=font)
        
        # Save the image
        img.save(current_image_path)
        
        # Refresh Preview using AppleScript
        applescript = f'''
        tell application "Preview"
            activate
            close every window
            delay 0.5
            open POSIX file "{current_image_path}"
        end tell
        '''
        subprocess.run(['osascript', '-e', applescript])
        time.sleep(0.5)
        
        return {
            "success": True,
            "message": f"Text '{text}' added at ({x},{y}) - visible in Preview"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Error adding text: {str(e)}"
        }

@mcp.tool()
def bring_preview_to_front() -> dict:
    """Bring Preview window to front so you can see the result."""
    print("CALLED: bring_preview_to_front()")
    try:
        applescript = '''
        tell application "Preview"
            activate
        end tell
        '''
        subprocess.run(['osascript', '-e', applescript])
        
        return {
            "success": True,
            "message": "Preview brought to front"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Error bringing Preview to front: {str(e)}"
        }
# DEFINE RESOURCES

# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    print("CALLED: get_greeting(name: str) -> str:")
    return f"Hello, {name}!"


# DEFINE AVAILABLE PROMPTS
@mcp.prompt()
def review_code(code: str) -> str:
    return f"Please review this code:\n\n{code}"
    print("CALLED: review_code(code: str) -> str:")


@mcp.prompt()
def debug_error(error: str) -> list[base.Message]:
    return [
        base.UserMessage("I'm seeing this error:"),
        base.UserMessage(error),
        base.AssistantMessage("I'll help debug that. What have you tried so far?"),
    ]

if __name__ == "__main__":
    # Check if running with mcp dev command
    print("STARTING")
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()  # Run without transport for dev server
    else:
        mcp.run(transport="stdio")  # Run with stdio for direct execution
