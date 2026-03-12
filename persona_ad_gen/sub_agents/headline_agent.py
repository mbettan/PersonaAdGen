# bettan_agent/sub_agents/headline_agent.py

from google.adk.tools import ToolContext
import google.genai as genai
import os

MODEL = "gemini-3.1-pro-preview"

async def generate_headlines_from_brief(tool_context: ToolContext) -> str:
    """
    Generates compelling headlines based on the persona-driven brief.
    """
    
    # Get the brief information from the tool context
    brief_data = tool_context.state.get("confirmed_brief", {})
    
    if not brief_data:
        return "❌ No brief found. Please complete the persona-driven brief first."
    
    ideal_customer = brief_data.get("ideal_customer", "")
    core_message = brief_data.get("core_message", "")
    tone_of_voice = brief_data.get("tone_of_voice", "")
    
    if not all([ideal_customer, core_message, tone_of_voice]):
        return "❌ Incomplete brief. Please ensure ideal customer, core message, and tone of voice are provided."
    
    print(f"🎯 Generating headlines for: {ideal_customer[:50]}...")
    print(f"📝 Core message: {core_message[:50]}...")
    print(f"🎭 Tone: {tone_of_voice}")
    
    try:
        # Get project information from environment
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT environment variable not set")
        
        # Initialize the client with Vertex AI configuration
        client = genai.Client(vertexai=True, project=project_id)
        
        # Create the headline generation prompt
        headline_prompt = f"""You are an expert advertising copywriter specializing in creating compelling headlines that convert.

Based on this persona-driven brief, generate 8-12 powerful headlines:

**Ideal Customer:** {ideal_customer}
**Core Message:** {core_message}
**Tone of Voice:** {tone_of_voice}

Create headlines that:
1. Speak directly to the ideal customer's pain points and desires
2. Capture the essence of the core message
3. Match the specified tone of voice
4. Are compelling and action-oriented
5. Vary in length and approach (some short and punchy, others more descriptive)
6. Include emotional triggers that resonate with the target audience

Generate headlines in different styles:
- Problem/Solution focused
- Benefit-driven
- Curiosity-inducing
- Social proof/testimonial style
- Urgency/scarcity driven
- Question-based
- Direct and bold statements

Format your response as a numbered list of headlines, each on a new line.
Focus on quality over quantity - each headline should be compelling and conversion-focused.

IMPORTANT: Only generate the numbered list of headlines. Do not include any other text, explanations, or formatting."""
        
        print(f"🤖 Calling Google Gen AI with prompt length: {len(headline_prompt)}")
        
        # Generate headlines using the same pattern as other tools
        response = client.models.generate_content(
            model=MODEL,
            contents=headline_prompt,
        )
        
        # Extract the text response
        result_text = response.text
        
        print(f"✅ LLM response received, length: {len(result_text)}")
        print(f"📝 Response preview: {result_text[:300]}...")
        
        # Parse the response to extract headlines
        headlines = []
        lines = result_text.strip().split('\n')
        print(f"🔍 Parsing {len(lines)} lines from response")
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                # Remove numbering/bullets and clean up
                headline = line
                # Remove common prefixes
                for prefix in ['1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '10.', '11.', '12.', '-', '•']:
                    if headline.startswith(prefix):
                        headline = headline[len(prefix):].strip()
                        break
                
                if headline and len(headline) > 5:  # Basic validation
                    headlines.append(headline)
                    print(f"    ✅ Added headline: '{headline}'")
        
        print(f"🎯 Found {len(headlines)} headlines after parsing")
        
        if len(headlines) < 5:
            print(f"❌ Not enough headlines generated. Only found {len(headlines)}")
            print(f"📝 Full LLM response for debugging:\n{result_text}")
            return f"❌ Could not generate enough quality headlines. Only found {len(headlines)} headlines. Generated response: {result_text[:500]}..."
        
        # Update the brief with generated headlines
        brief_data["headlines"] = headlines[:12]  # Limit to 12 headlines
        tool_context.state["confirmed_brief"] = brief_data
        
        # Format the response
        headline_list = '\n'.join([f"• {headline}" for headline in headlines[:12]])
        
        return f"""✅ **Generated {len(headlines[:12])} Compelling Headlines**

{headline_list}

**Headlines Analysis:**
• **Target Audience:** {ideal_customer}
• **Core Message:** {core_message}
• **Tone:** {tone_of_voice}

These headlines have been automatically added to your brief. You can now proceed with image generation or make any adjustments if needed.

**Next Steps:**
1. Review the generated headlines
2. Upload your base image if you haven't already
3. Proceed with creating your advertising scenes

Ready to create compelling ads that convert!"""
        
    except Exception as e:
        print(f"❌ Error in generate_headlines_from_brief: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"❌ Error generating headlines: {str(e)}. Please try again or provide headlines manually."
