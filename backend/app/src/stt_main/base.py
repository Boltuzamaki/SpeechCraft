from abc import ABC, abstractmethod


class BaseSTT(ABC):
    """Abstract Base Class for Speech-to-Text models."""

    def __init__(self, audio_data, audio_metadata):
        self.audio_data = audio_data
        self.audio_metadata = audio_metadata

    @abstractmethod
    async def audio_preprocessing(self):
        """Preprocess raw audio data before transcription.

        Args:
            audio_data: Raw audio input.

        Returns:
            Processed audio data ready for STT.
        """
        pass

    @abstractmethod
    async def transcribe(self):
        """Convert processed audio into text.

        Args:
            audio_data: Preprocessed audio input.

        Returns:
            Transcribed text (string).
        """
        pass
