from app.src.stt_main.factory import STTFactory


async def main(**kwargs) -> dict:
    """
    Asynchronous main driver function to process and transcribe audio.
    This function now raises exceptions on failure instead of returning
    strings.

    Args:
        **kwargs: Dictionary containing audio data and metadata.

    Returns:
        dict: The transcription result dictionary.

    Raises:
        ValueError: If required parameters are missing.
        Exception: Propagates exceptions from the STT processor.
    """
    stt_type = kwargs.get("stt_type", "whisper")
    audio_data = kwargs.get("audio_data")

    audio_metadata = {
        k: v
        for k, v in kwargs.items()
        if k not in ["audio_data", "callback_url"]
    }

    if not audio_data:
        raise ValueError("Missing required 'audio_data' in request.")

    stt_processor = STTFactory.create_stt_processor(
        stt_type=stt_type,
        audio_data=audio_data,
        audio_metadata=audio_metadata,
    )

    result_dict = await stt_processor.transcribe()
    return result_dict
