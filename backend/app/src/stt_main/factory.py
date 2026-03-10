import importlib


class STTFactory:
    """Factory class to create STT processors dynamically."""

    # Dictionary mapping STT technique names to their respective classes
    STT_CLASSES = {
        "whisper": "app.src.stt_main.whisperSTT.whisperstt.WhisperSTT",
        # Future additions like "deepspeech":
        # "app.src.stt_main.deepspeechSTT.DeepSpeechSTT"
    }

    @staticmethod
    def create_stt_processor(
        stt_type: str,
        audio_data,
        audio_metadata,
        **kwargs,
    ):
        """
        Factory method to create an STT processor instance.

        Args:
            stt_type (str): The type of STT processor (case-insensitive).
            audio_data (str): Base64-encoded audio data.
            audio_metadata (dict): Metadata for the audio.

        Returns:
            An instance of the specified STT processor class.

        Raises:
            ValueError: If the STT processor class cannot be found or imported.
        """
        stt_type_lower = stt_type.lower()

        # Check if the STT type is registered in the factory
        if stt_type_lower in STTFactory.STT_CLASSES:
            module_path, class_name = STTFactory.STT_CLASSES[
                stt_type_lower
            ].rsplit(".", 1)
        else:
            # Dynamically import from a standard module structure
            # if not predefined
            module_path = f"app.src.stt_main.{stt_type_lower}STT"
            class_name = f"{stt_type.capitalize()}STT"

        try:
            module = importlib.import_module(module_path)
            stt_class = getattr(module, class_name)
        except (ImportError, AttributeError) as e:
            raise ValueError(
                f"STT class '{class_name}' not found in module '{module_path}'."  # noqa
            ) from e

        # Instantiate the STT class with the provided audio data and metadata
        instance = stt_class(
            audio_data,
            audio_metadata,
            kwargs=kwargs,
        )
        return instance
