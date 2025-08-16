# backend/utils/image_ai.py
import openai
from openai import OpenAI
import requests
from PIL import Image  # imported for potential local edits, not currently used
from io import BytesIO  # imported for potential in-memory handling, not currently used
import os

# API key is loaded from environment (never hardcode!)
# In local dev, put OPENAI_API_KEY=... in .env
# In production (AWS App Runner / ECS), set it in the service environment variables.
openai.api_key = os.getenv("OPENAI_API_KEY")


def process_image(input_path: str, output_path: str, edit_type: str, intensity: int):
    """
    Process an image using OpenAI's image APIs.
    Parameters:
      input_path: local path to the uploaded file
      output_path: where to save the processed image
      edit_type: one of the supported modes ("enhance", "restore", "retouch", "style", "background")
      intensity: integer used for "strength" (currently unused in the OpenAI call)
    """

    # Rich, descriptive prompts for each supported edit type
    prompts = {
        "enhance": (
            "Apply professional-grade image enhancement with advanced sharpening algorithms, "
            "noise reduction, and detail amplification. Optimize contrast, brightness, and color "
            "saturation while preserving natural skin tones and preventing over-processing artifacts."
        ),
        "restore": (
            "Perform comprehensive image restoration using state-of-the-art denoising, deblurring, "
            "and artifact removal techniques. Reconstruct missing details, eliminate compression "
            "artifacts, reduce motion blur, and restore original image quality with photorealistic precision."
        ),
        "retouch": (
            "Execute professional portrait retouching with advanced blemish removal, skin smoothing, "
            "and complexion enhancement. Eliminate imperfections, reduce wrinkles, brighten eyes, "
            "whiten teeth, and perfect skin texture while maintaining natural appearance."
        ),
        "style": (
            "Transform the image into a masterpiece oil painting with rich textures, vibrant brush "
            "strokes, and classical artistic techniques. Apply layered paint effects, canvas texture, "
            "and traditional color palettes while preserving subject recognition."
        ),
        "background": (
            "Perform precision background removal using advanced AI segmentation with sub-pixel accuracy. "
            "Create clean transparent PNG output with perfect edge detection, hair detail preservation, "
            "and anti-aliasing for professional compositing results."
        ),
    }

    # Validate edit type
    if edit_type not in prompts:
        raise ValueError(f"Unsupported edit_type: {edit_type}")

    prompt = prompts[edit_type]  # currently not passed to API (see note below)

    # Create an OpenAI client
    client = OpenAI()

    # For now, the code always uses create_variation (ignores prompt + intensity).
    # You might replace this with client.images.edit() to apply custom prompts,
    # or pass `prompt=prompt` into the request if your API version supports it.
    response = client.images.create_variation(
        image=open(input_path, "rb"),
        n=1,
        size="512x512"
    )

    # Download the generated image
    image_url = response.data[0].url
    img_data = requests.get(image_url).content

    # Save it to output_path
    with open(output_path, "wb") as f:
        f.write(img_data)

    print("Image saved to:", output_path)
    print("Generated image URL:", image_url)
