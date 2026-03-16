import os
import time
import asyncio
from google import genai
from google.genai import types

async def generate_final_video():
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "your-project-id")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
    client = genai.Client(vertexai=True, project=project_id, location=location)

    image_path = "outputs/scene4_accomplished.jpg"
    if not os.path.exists(image_path):
        print(f"Error: {image_path} not found.")
        return

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    prompt = "A cinematic shot of a hiker conquering a rainy PNW trail, high-tech durable gear, inspiring lighting."
    
    print(f"🚀 Generating video from {image_path}...")
    source = types.GenerateVideosSource(
        prompt=prompt,
        image=types.Image(image_bytes=image_bytes, mime_type="image/jpeg")
    )
    video_config = types.GenerateVideosConfig(
        aspect_ratio="16:9", number_of_videos=1, duration_seconds=5, resolution="720p"
    )
    
    operation = client.models.generate_videos(
        model="veo-3.1-generate-001",
        source=source,
        config=video_config
    )
    
    print(f"Operation name: {operation.name}")
    start_time = time.time()
    while not operation.done:
        print(f"Waiting... ({int(time.time() - start_time)}s)")
        await asyncio.sleep(20)
        try:
            operation = client.operations.get(operation)
        except:
             operation = client.operations.get(name=operation.name)
    
    if operation.result and operation.result.generated_videos:
        video_obj = operation.result.generated_videos[0]
        out_video = "outputs/final_example_video.mp4"
        client.files.download(file=video_obj.video, destination=out_video)
        print(f"✅ Saved video to {out_video}")
    else:
        print("❌ Video generation failed.")

if __name__ == "__main__":
    asyncio.run(generate_final_video())
