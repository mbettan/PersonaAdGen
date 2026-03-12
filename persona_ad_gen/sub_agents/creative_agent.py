# bettan_agent/sub_agents/creative_agent.py

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
# Import the new editing tool
from ..tools import edit_scene_image

MODEL = "gemini-3.1-pro-preview"

class CreativeAgent(LlmAgent):
    """A sub-agent specializing in generating editing plans and executing them."""
    def __init__(self):
        super().__init__(
            name="creative_agent",
            model=MODEL,
            description="A creative specialist that takes a confirmed brief and a base image, then generates and applies a 4-scene editing plan.",
            instruction=(
                "You are a world-class visual editor. The user has confirmed their brief and provided a base image.\n\n"
                "**Your Workflow:**\n"
                "1. The base image has already been saved as 'user:base_image.png' (or similar extension).\n"
                "2. First, analyze the confirmed brief and generate a creative 4-scene editing plan.\n"
                "3. **IMPORTANT**: First, present the complete storyline and scene descriptions to the user.\n"
                "4. Display the headlines that were generated for this brief.\n"
                "5. Show the 4-scene plan with detailed storylines.\n"
                "6. After presenting the plan, IMMEDIATELY call the `edit_scene_image` tool for each of the 4 scenes to generate the images.\n\n"
                "**Confirmed Brief:**\n{confirmed_brief}\n\n"
                "**Your Response Format:**\n"
                "1. Start with: '🎬 **Creative Storyline Plan**'\n"
                "2. Show the generated headlines\n"
                "3. Present the 4-scene plan with:\n"
                "   - Scene 1: [Scene Name]\n"
                "     Story: [What story this scene tells]\n"
                "     Visual Description: [Detailed visual description]\n"
                "   - Scene 2: [Scene Name]\n"
                "     Story: [What story this scene tells]\n"
                "     Visual Description: [Detailed visual description]\n"
                "   - Scene 3: [Scene Name]\n"
                "     Story: [What story this scene tells]\n"
                "     Visual Description: [Detailed visual description]\n"
                "   - Scene 4: [Scene Name]\n"
                "     Story: [What story this scene tells]\n"
                "     Visual Description: [Detailed visual description]\n"
                "4. After presenting the plan, end with: 'Now, I will generate the 4 advertising scenes for you.'\n"
                "5. Do NOT wait for user confirmation. Call the `edit_scene_image` tool for each scene immediately after presenting the plan.\n\n"
                "**Important Notes:**\n"
                "- Each scene should tell a part of the advertising story that builds toward the core message.\n"
                "- Consider the ideal customer and tone of voice when creating scenes.\n"
                "- Make the scenes progressively build a narrative that resonates with the target audience.\n"
                "- The visual descriptions should be specific and detailed to guide the image generation."
            ),
            # This agent's only tool is the image editor
            tools=[FunctionTool(func=edit_scene_image)]
        )
