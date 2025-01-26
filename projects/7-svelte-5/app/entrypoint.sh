#!/bin/sh

# Handle docker volmue mapping for pip
if ! command -v pip &> /dev/null
then
    echo "pip could not be found. Reinstalling..."
    python -m ensurepip
    pip install -r requirements.txt
    python -c "import nltk; nltk.download('popular'); nltk.download('punkt_tab'); nltk.download('averaged_perceptron_tagger_eng')"
fi

if [ "${APP_USE_FLASH_ATTENTION}" = "TRUE" ]; then
    echo "APP_USE_FLASH_ATTENTION is TRUE. Installing flash-attn..."
    pip install flash-attn --no-build-isolation
fi

exec "$@"
