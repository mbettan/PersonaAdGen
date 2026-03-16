import os
import time
from google import genai
from google.genai import types

def generate_examples():
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "your-project-id")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
    client = genai.Client(vertexai=True, project=project_id, location=location)

    prompt = "A cinematic shot of a hiker conquering a rainy PNW trail, high-tech durable gear, inspiring lighting."
    
    print("🎨 Generating example image...")
    # Generate Image
    response = client.models.generate_images(
        model="imagen-3.0-generate-002",
        prompt=prompt,
        config=types.GenerateImagesConfig(number_of_images=1)
    )
    
    if response.generated_images:
        img = response.generated_images[0]
        image_bytes = img.image.image_bytes
        with open("example_scene.png", "wb") as f:
            f.write(image_bytes)
        print("✅ Saved example_scene.png")
        
        # Generate Video from that image
        print("🚀 Generating example video (this takes ~2 mins)...")
        source = types.GenerateVideosSource(
            prompt=prompt,
            image=types.Image(image_bytes=image_bytes, mime_type="image/png")
        )
        video_config = types.GenerateVideosConfig(
            aspect_ratio="16:9", number_of_videos=1, duration_seconds=5, resolution="720p"
        )
        operation = client.models.generate_videos(
            model="veo-3.1-fast-generate-preview",
            source=source,
            config=video_config
        )
        
        while not operation.done:
            time.sleep(15)
            operation = client.operations.get(operation)
        
        if operation.result and operation.result.generated_videos:
            video_obj = operation.result.generated_videos[0]
            client.files.download(file=video_obj.video, destination="example_video.mp4")
            print("✅ Saved example_video.mp4")
        else:
            print("❌ Video generation failed.")
    else:
        print("❌ Image generation failed.")

if __name__ == "__main__":
    generate_examples()
