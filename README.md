# 🍄 Dr. Fungi

**⚠️ This is a demonstration project only - do not use for actual mushroom identification or foraging decisions.**

## Overview

Dr. Fungi is an AI-powered mycologist with 30+ years of simulated expertise in mushroom identification, foraging safety, cultivation, and culinary preparation. Upload photos for instant mushroom identification with structured analysis data, or ask questions about fungi-related topics.

## Features

- **🔍 Image Analysis**: Upload mushroom photos for identification and detailed analysis
- **📊 Structured Data**: Extracts JSON data including species, confidence, edibility, and visible features
- **⚠️ Safety First**: Emphasizes foraging safety and proper identification practices
- **💬 Expert Chat**: Ask questions about cultivation, cooking, ecology, and mycology
- **🎯 Specialized Knowledge**: Domain-specific responses with mycological expertise
- **⚡ Real-time Streaming**: Live response streaming for better user experience

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/Dr.Fungi.git
   cd Dr.Fungi
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

## Usage

### Image Analysis
- Upload a mushroom photo using the image input
- Optionally add a specific question about the image
- Receive identification with structured JSON data including:
  - Common name and genus
  - Confidence level
  - Visible parts (cap, hymenium, stipe)
  - Color analysis
  - Edibility assessment

### Chat Interface
- Ask questions about mushroom identification, foraging, cultivation, or cooking
- Get expert advice on safety practices
- Learn about fungi ecology and medicinal properties
- Receive contextual responses based on previous image analysis

## JSON Output Format

When analyzing images, Dr. Fungi provides structured data:

```json
{
  "common_name": "Oyster Mushroom",
  "genus": "Pleurotus",
  "confidence": 0.85,
  "visible": ["cap", "hymenium"],
  "color": "light brown",
  "edible": true
}
```

## Requirements

- Python 3.8+
- Anthropic API key
- Required packages (see requirements.txt):
  - gradio
  - anthropic
  - python-dotenv
  - Pillow

## Safety Disclaimer

⚠️ **Important**: This tool is for educational and informational purposes only. Never consume wild mushrooms based solely on AI identification. Always consult with local mycologists and use multiple field guides before foraging or consuming any wild fungi.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [Claude API](https://www.anthropic.com/claude) by Anthropic
- UI powered by [Gradio](https://gradio.app/)
- Inspired by the mycology community and safe foraging practices
