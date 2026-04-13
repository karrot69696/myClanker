#!/usr/bin/env python3
"""
Simple high-speed transcription using faster-whisper-base.
Optimized for download speed using HF_TOKEN.
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Try to use hf_transfer for much faster downloads if available
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"

try:
    from faster_whisper import WhisperModel
except ImportError:
    print(json.dumps({"error": "faster-whisper not installed. Please install it with 'pip install faster-whisper hf_transfer'"}))
    sys.exit(1)


def transcribe(audio_path: Path, model_size: str = "turbo") -> dict:
    """
    Transcribe audio with faster-whisper.
    """
    # Use HF_TOKEN if available in environment
    hf_token = os.environ.get("HF_TOKEN")
    
    # Try to login for authenticated high-speed downloads
    if hf_token:
        try:
            from huggingface_hub import login
            login(token=hf_token)
        except ImportError:
            pass

    # Initialize model
    # device="auto" allows GPU if available (CUDA)
    # compute_type="int8" is the fastest for CPU
    try:
        model = WhisperModel(
            model_size, 
            device="auto", 
            compute_type="int8", 
            download_root=None, # uses default HF cache
        )
    except Exception as e:
        return {"error": f"Failed to load model: {str(e)}"}

    # Transcribe
    segments, info = model.transcribe(str(audio_path), beam_size=5, vad_filter=True)
    
    transcription_data = {
        "text": "",
        "segments": [],
        "language": info.language,
        "language_probability": info.language_probability,
        "duration": info.duration,
    }

    full_text = []
    for segment in segments:
        full_text.append(segment.text.strip())
        transcription_data["segments"].append({
            "start": round(segment.start, 2),
            "end": round(segment.end, 2),
            "text": segment.text.strip()
        })
    
    transcription_data["text"] = " ".join(full_text)
    return transcription_data


def parse_args():
    parser = argparse.ArgumentParser(description="Transcribe audio using faster-whisper")
    parser.add_argument("audio_path", help="Path to the audio file")
    parser.add_argument("--model", default="turbo", help="Whisper model size (turbo, large-v3, medium, small, base, tiny)")
    return parser.parse_args()


def main():
    args = parse_args()
    audio_path = Path(args.audio_path).expanduser().resolve()
    
    if not audio_path.exists():
        print(json.dumps({"error": f"Audio file not found: {audio_path}"}))
        sys.exit(1)

    result = transcribe(audio_path, args.model)
    
    if "error" in result:
        print(json.dumps(result))
        sys.exit(1)
        
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
