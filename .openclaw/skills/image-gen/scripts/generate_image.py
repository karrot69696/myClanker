#!/usr/bin/env python3
"""
Quick image generation script using Pollinations.AI
Usage: python generate_image.py "your prompt here" [output_path]
"""
import sys
import urllib.parse
import urllib.request

POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}?nologo=true&enhance=true&model=flux-realism"

def generate_image(prompt, output_path=None):
    if not prompt:
        print("Error: No prompt provided", file=sys.stderr)
        sys.exit(1)
    
    # default output path
    if not output_path:
        safe_name = "".join(c if c.isalnum() or c in (' ', '_') else '_' for c in prompt)
        safe_name = safe_name[:50].strip().replace(' ', '_')
        output_path = f"/root/.openclaw/workspace/generated_{safe_name}.png"
    
    encoded = urllib.parse.quote(prompt)
    url = POLLINATIONS_URL.format(prompt=encoded)
    
    print(f"Generating: {prompt}", file=sys.stderr)
    print(f"URL: {url}", file=sys.stderr)
    
    try:
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        with urllib.request.urlopen(req, timeout=90) as response:
            image_data = response.read()
        
        with open(output_path, 'wb') as f:
            f.write(image_data)
        
        # output just the path for easy capture
        print(output_path)
        return output_path
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_image.py 'your prompt' [output_path]", file=sys.stderr)
        sys.exit(1)
    
    prompt = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else None
    generate_image(prompt, output)
