import asyncio
import base64
import os
import tempfile

import aiofiles
import whisper

from app.src.stt_main.base import BaseSTT

__all__ = [
    "WhisperSTT",
]


class WhisperSTT(BaseSTT):
    _models = {}

    def __init__(
        self,
        audio_data,
        audio_metadata,
        **kwargs,
    ):
        """Initialize with Base64 audio data and metadata."""
        super().__init__(
            audio_data,
            audio_metadata,
        )

        self.model_name = self.audio_metadata.get(
            "model_name",
            "base",
        )

        # Load the model once per model type and reuse it
        if self.model_name not in WhisperSTT._models:
            WhisperSTT._models[self.model_name] = whisper.load_model(
                self.model_name
            )

        # Use the already loaded model
        self.model = WhisperSTT._models[self.model_name]
        self.kwargs = kwargs

    async def audio_preprocessing(self):
        """Asynchronously decode Base64 audio and save as a temporary
        WAV file."""
        try:
            # Decode Base64 in an async-safe way
            audio_bytes = await asyncio.to_thread(
                base64.b64decode,
                self.audio_data,
            )

            # Create a temporary WAV file (Async File Writing)
            temp_file = await asyncio.to_thread(
                tempfile.NamedTemporaryFile,
                delete=False,
                suffix=".wav",
            )

            # Write the decoded bytes to the temp file asynchronously
            async with aiofiles.open(
                temp_file.name,
                "wb",
            ) as f:
                await f.write(audio_bytes)

            return temp_file.name  # Return the file path

        except Exception as e:
            raise RuntimeError(f"Audio processing failed: {e}")

    async def transcribe(self):
        """Asynchronously transcribe processed audio using Whisper and
        return text."""
        try:
            audio_file = (
                await self.audio_preprocessing()
            )  # Convert Base64 to WAV

            # Transcribe using Whisper in a separate thread
            result = await asyncio.to_thread(
                self.model.transcribe,
                audio_file,
            )
            transcribed_text = result

            # Cleanup: Delete temp file asynchronously after processing
            await asyncio.to_thread(
                os.remove,
                audio_file,
            )

            return {
                "transcribed_text": transcribed_text,
                "task_id": self.kwargs.get("task_id", None),
            }

        except Exception as e:
            raise RuntimeError(f"Transcription failed: {e}")
