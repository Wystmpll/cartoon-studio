#!/bin/bash
# One-time setup of free local narration on a Mac with Apple Silicon (M1 or newer, 16 GB RAM recommended).
# Run in Terminal from the voice folder:   cd ~/CartoonVoice && bash setup.sh
# Needs internet (a VPN in mainland China) for the first run: downloads ~1-5 GB of models from Hugging Face.
set -e
cd "$(dirname "$0")"
if ! command -v brew >/dev/null; then
  echo "Installing Homebrew (asks for your Mac password)..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  eval "$(/opt/homebrew/bin/brew shellenv)"
fi
brew list python@3.11 >/dev/null 2>&1 || brew install python@3.11
brew list ffmpeg >/dev/null 2>&1 || brew install ffmpeg
PY=$(brew --prefix python@3.11)/bin/python3.11
[ -d .venv ] || $PY -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install "qwen-tts-cli[mlx]" edge-tts
mkdir -p presets jobs
echo "Downloading models and creating 4 starter voices (first time is slow)..."
python voice.py design narrator_deep  "Deep, calm, low male narrator voice, documentary style, slow and tense, dramatic pauses" --lang ru
python voice.py design narrator_young "Young energetic male voice, clear and fast, slightly ironic storyteller" --lang ru
python voice.py design narrator_female "Warm, confident female narrator, mysterious, medium pitch, cinematic" --lang ru
python voice.py design narrator_en    "Deep cinematic male trailer narrator, calm and tense" --lang en
echo "DONE. Voices:"; python voice.py presets
