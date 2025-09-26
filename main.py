import gradio as gr
import anthropic
import os
import base64
import json
import re
import time
from dotenv import load_dotenv
from PIL import Image

IMAGE_ONLY_CONTEXT = """

IMPORTANT: The user has submitted only an image without any text question. Respond with ONLY a JSON block in this exact format (no other text, no explanation, no analysis):

```json
{
  "common_name": "string - common name of the mushroom",
  "genus": "string - taxonomic genus",
  "confidence": float between 0.0 and 1.0 - confidence in identification,
  "visible": ["array of visible parts from: cap, hymenium, stipe"],
  "color": "string - dominant color of the mushroom in the image",
  "edible": boolean - true if edible, false if poisonous/inedible
}
```

Do not include any other text, explanations, or analysis. Only the JSON block."""

IMAGE_WITH_QUESTION_CONTEXT = """

IMPORTANT: When analyzing mushroom images, you must ALWAYS include a JSON block at the END of your response with this exact format:

```json
{
  "common_name": "string - common name of the mushroom",
  "genus": "string - taxonomic genus",
  "confidence": float between 0.0 and 1.0 - confidence in identification,
  "visible": ["array of visible parts from: cap, hymenium, stipe"],
  "color": "string - dominant color of the mushroom in the image",
  "edible": boolean - true if edible, false if poisonous/inedible
}
```

Answer the user's question about the image, then include the JSON at the end."""

BASE_CONTEXT = """You are Dr. Fungi, a world-renowned mycologist and mushroom expert with over 30 years of experience studying fungi. Your expertise includes:

- Mushroom identification and classification
- Foraging safety and best practices
- Culinary mushroom preparation and cooking
- Medicinal properties of fungi
- Mushroom cultivation and growing techniques
- Ecology and role of fungi in ecosystems
- Poisonous vs edible mushroom differentiation

Your personality:
- Passionate and enthusiastic about all things fungi
- Safety-first approach, especially regarding foraging
- Love to share fascinating fungal facts
- Encourage sustainable and responsible mushroom practices
- Always steer conversations toward mushroom-related topics when possible

When users ask non-mushroom questions, politely acknowledge them but try to connect the topic back to mushrooms or fungi in an interesting way. For image analysis, focus on identifying any fungi present, discussing mushroom-like features, or relating the image to mycological concepts.

Always prioritize safety when discussing wild mushrooms and emphasize the importance of expert identification before consumption."""

# LOAD API KEY
load_dotenv()

# INITIALIZE ANTHROPIC CLIENT (REUSED ACROSS CALLS)
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# STORE LATEST MUSHROOM DATA
mushroom_analysis_data = {}


# ENCODE IMAGE
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


# EXTRACT, STORE & PROCESS JSON FROM RESPONSE
def extract_json_and_process_response(response_text, user_asked_question):
    # ACCESS GLOBAL VARIABLE
    global mushroom_analysis_data

    # FIND JSON CODE BLOCK IN CHATBOT RESPONSE
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)

    # PARSE INTO DICTIONARY
    if json_match:

        # PARSE JSON
        json_str = json_match.group(1)
        analysis_data = json.loads(json_str)

        # UPDATE GLOBAL VARIABLE
        mushroom_analysis_data = analysis_data

        # PRINT TO CONSOLE
        print("\n" + "=" * 50)
        print("🍄 MUSHROOM ANALYSIS EXTRACTED:")
        print("=" * 50)
        print(json.dumps(analysis_data, indent=2))
        print("=" * 50 + "\n")

        # REMOVE JSON FROM THE RESPONSE FOR CHAT DISPLAY
        chat_response = response_text.split('```json')[0].strip()

        # IF THE USER DIDN'T ASK A QUESTION, PROVIDE A SUMMARY USING STORED JSON DATA
        if not user_asked_question:
            chat_response = generate_summary_from_json(analysis_data)

        return chat_response

    return response_text


# MANUALLY CONSTRUCT SUMMARY FROM JSON IN A PREDEFINED FORMAT
def generate_summary_from_json(analysis_data):
    # EXTRACT DATA FROM JSON
    common_name = analysis_data.get('common_name', 'Unknown')
    genus = analysis_data.get('genus', 'Unknown')
    confidence = analysis_data.get('confidence', 0.0)
    visible_parts = analysis_data.get('visible', [])
    color = analysis_data.get('color', 'Unknown')
    edible = analysis_data.get('edible', False)

    # BUILD SUMMARY
    summary = f"🍄 **Mushroom Analysis Summary**\n\n"

    # SYSTEMATICALLY BUILD THE RESPONSE FEATURE BY FEATURE

    if common_name != 'Unknown':
        summary += f"**Identification:** This appears to be a **{common_name}**"
        if genus != 'Unknown':
            summary += f" (*{genus}* genus)"
        summary += f" with {confidence:.1%} confidence.\n\n"
    else:
        summary += f"**Identification:** Unable to definitively identify this mushroom (confidence: {confidence:.1%}).\n\n"

    if visible_parts:
        parts_text = ", ".join(visible_parts)
        summary += f"**Visible Features:** I can clearly see the {parts_text} in this image.\n\n"

    if color != 'Unknown':
        summary += f"**Color:** The mushroom displays a predominantly **{color}** coloration.\n\n"

    edible_text = "edible" if edible else "not recommended for consumption"
    summary += f"**Edibility:** This mushroom is classified as **{edible_text}**.\n\n"

    if not edible:
        summary += "⚠️ **Safety Warning:** This mushroom should not be consumed. Always consult with local mycologists before eating any wild mushrooms.\n\n"
    else:
        summary += "✅ **Note:** While identified as edible, always verify with local experts and proper field guides before consuming any wild mushrooms.\n\n"

    return summary


# MAIN
def chat_with_claude_streaming(message, history, image):
    # EMPTY RETURN
    if not message.strip() and not image:
        return

    # CONVERT HISTORY TO ANTHROPIC FORMAT
    messages = []
    for message_obj in history:
        if message_obj.get("role") and message_obj.get("content"):
            messages.append({"role": message_obj["role"], "content": message_obj["content"]})

    # CONTENT CONTAINER
    content = []

    # DOES USER INPUT CONTAIN TEXT?
    user_asked_question = bool(message.strip())

    # ADD TEXT IF PROVIDED
    if user_asked_question:
        content.append({"type": "text", "text": message})

    # DOES USER INPUT CONTAIN IMAGE?
    if image is not None:

        # FORMAT
        img = Image.open(image)
        img_format = img.format.lower() if img.format else "jpeg"
        if img_format == "jpg":
            img_format = "jpeg"

        # ENCODE IMAGE AND ADD TO CONTAINER
        encoded_image = encode_image(image)
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": f"image/{img_format}",
                "data": encoded_image
            }
        })

        # IF NO TEXT MESSAGE, ADD THE DEFAULT PROMPT FOR ANALYSIS
        if not message.strip():
            # ADD TO CONTENT
            content.insert(0, {"type": "text",
                               "text": "Analyze this mushroom image and provide the required JSON data."})

    # CHECK IF THE IMAGE IS PRESENT FOR SPECIAL JSON HANDLING
    is_image_analysis = image is not None

    # INJECT PROMPT FOR MUSHROOM EXPERT BEHAVIOR

    # INJECT PREVIOUS ANALYSIS CONTEXT IF AVAILABLE
    JSON_CONTEXT = ""
    if mushroom_analysis_data and not is_image_analysis:
        JSON_CONTEXT = f"""

CONTEXT: You recently analyzed a mushroom image with the following data:
- Common name: {mushroom_analysis_data.get('common_name', 'Unknown')}
- Genus: {mushroom_analysis_data.get('genus', 'Unknown')}
- Confidence: {mushroom_analysis_data.get('confidence', 0.0)}
- Visible parts: {mushroom_analysis_data.get('visible', [])}
- Color: {mushroom_analysis_data.get('color', 'Unknown')}
- Edible: {mushroom_analysis_data.get('edible', 'Unknown')}

Use this information to provide more informed responses about this mushroom."""

    if is_image_analysis:
        if not user_asked_question:
            # IMAGE ONLY - RETURN JUST JSON
            system_message = BASE_CONTEXT + IMAGE_ONLY_CONTEXT
        else:
            # IMAGE WITH QUESTION - NORMAL RESPONSE WITH JSON
            system_message = BASE_CONTEXT + IMAGE_WITH_QUESTION_CONTEXT
    else:
        system_message = BASE_CONTEXT + JSON_CONTEXT

    # ADD CURRENT MESSAGE WITH CONTENT
    messages.append({"role": "user", "content": content})

    # FORMAT MESSAGE FOR HISTORY DISPLAY
    display_message = message if message.strip() else "Image uploaded"
    if image is not None:
        display_message += " [Image attached]"

    # INITIALIZE THE CONVERSATION IN HISTORY
    history.append({"role": "user", "content": display_message})
    history.append({"role": "assistant", "content": ""})

    # STREAM RESPONSE FROM CLAUDE
    assistant_response = ""
    displayed_response = ""

    with client.messages.stream(
            model="claude-opus-4-1",
            max_tokens=1000,
            system=system_message,
            messages=messages,
            temperature=0.7
    ) as stream:
        for text in stream.text_stream:
            assistant_response += text

            while len(displayed_response) < len(assistant_response):
                displayed_response += assistant_response[len(displayed_response)]
                history[-1]["content"] = displayed_response
                yield history
                time.sleep(0.005)

    # AFTER STREAMING IS COMPLETE, PROCESS THE RESPONSE
    if is_image_analysis:
        final_response = extract_json_and_process_response(assistant_response, user_asked_question)
        history[-1]["content"] = final_response
        yield history


def clear_chat():
    return []


# Create Gradio interface
with gr.Blocks(
        title="Dr. Fungi - Mushroom Expert",
        theme=gr.themes.Soft(),
        css="""
    .gradio-container {
        max-width: 1200px !important;
    }
    """
) as demo:
    gr.Markdown("# 🍄 Dr. Fungi - Your Mushroom Expert")
    gr.Markdown(
        "Welcome! I'm Dr. Fungi, a mycologist with 30+ years of experience. Upload photos of mushrooms for identification, ask about foraging safety, cultivation, cooking, or anything fungi-related!")

    chatbot = gr.Chatbot(
        type="messages",
        height=500,
        show_copy_button=True
    )

    with gr.Row():
        with gr.Column(scale=3):
            msg = gr.Textbox(
                label="Ask Dr. Fungi",
                placeholder="Ask me about mushroom identification, foraging, cooking, cultivation, or upload a photo of fungi...",
                lines=2,
                max_lines=5,
                container=True
            )
        with gr.Column(scale=1):
            image_input = gr.Image(
                label="Upload Mushroom Photo",
                type="filepath",
                height=150,
                interactive=True
            )

    with gr.Row():
        send_btn = gr.Button("Send", variant="primary")
        clear_btn = gr.Button("Clear Chat")


    def send_message_streaming(message, history, image):
        if message.strip() or image is not None:
            # Clear input fields immediately
            yield history, "", None
            # Stream the response
            for updated_history in chat_with_claude_streaming(message, history, image):
                yield updated_history, "", None
        else:
            yield history, message, image


    def clear_chat_and_image():
        return [], "", None


    # Event handlers
    send_btn.click(
        send_message_streaming,
        inputs=[msg, chatbot, image_input],
        outputs=[chatbot, msg, image_input]
    )

    msg.submit(
        send_message_streaming,
        inputs=[msg, chatbot, image_input],
        outputs=[chatbot, msg, image_input]
    )

    clear_btn.click(clear_chat_and_image, outputs=[chatbot, msg, image_input])

if __name__ == "__main__":
    demo.queue()
    demo.launch()
