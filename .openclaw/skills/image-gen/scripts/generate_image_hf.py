#!/usr/bin/env python3
"""
Hugging Face image generation using Animagine XL models via InferenceClient
Usage: python generate_image_hf.py "your prompt here" [output_path]
"""
import os
import sys
from huggingface_hub import InferenceClient

HF_TOKEN = os.getenv("HF_TOKEN", "")
PRIMARY_MODEL = "cagliostrolab/animagine-xl-4.0"
FALLBACK_MODEL = "cagliostrolab/animagine-xl-3.1"

def generate_image(prompt, output_path=None, model=PRIMARY_MODEL):
    if not prompt:
        print("Error: No prompt provided", file=sys.stderr)
        sys.exit(1)
    
    # default output path
    if not output_path:
        safe_name = "".join(c if c.isalnum() or c in (' ', '_') else '_' for c in prompt)
        safe_name = safe_name[:50].strip().replace(' ', '_')
        output_path = f"/root/.openclaw/workspace/generated_{safe_name}.png"
    
    print(f"Generating with {model}: {prompt}", file=sys.stderr)
    
    # create client with token
    client = InferenceClient(token=HF_TOKEN)
    
    try:
        # generate image
        image = client.text_to_image(prompt, model=model)
        
        # save image
        image.save(output_path)
        print(output_path)
        return output_path
        
    except Exception as e:
        import traceback
        print(f"Error: {e}", file=sys.stderr)
        print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
        raise

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_image_hf.py 'your prompt' [output_path]", file=sys.stderr)
        sys.exit(1)
    
    prompt = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        generate_image(prompt, output, PRIMARY_MODEL)
    except Exception as e:
        print(f"Primary model failed: {e}", file=sys.stderr)
        print(f"Falling back to {FALLBACK_MODEL}...", file=sys.stderr)
        try:
            generate_image(prompt, output, FALLBACK_MODEL)
        except Exception as e2:
            print(f"Fallback model also failed: {e2}", file=sys.stderr)
            sys.exit(1)
