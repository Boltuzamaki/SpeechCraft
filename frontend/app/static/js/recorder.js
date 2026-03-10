/**
 * AudioRecorder — Single Responsibility: MediaRecorder lifecycle only.
 * Produces a standard File object; has no knowledge of the DOM or UI.
 */
class AudioRecorder {
    constructor() {
        this._mediaRecorder = null;
        this._chunks = [];
        this._stream = null;
        this._blob = null;
        this._mimeType = '';
    }

    get isRecording() {
        return this._mediaRecorder?.state === 'recording';
    }

    get blob() {
        return this._blob;
    }

    /**
     * Requests microphone access and starts recording.
     * @returns {MediaStream} — callers may use this to drive a visualizer.
     */
    async start() {
        this._chunks = [];
        this._blob = null;

        this._stream = await navigator.mediaDevices.getUserMedia({ audio: true });

        // Pick the best supported container
        const candidates = [
            'audio/webm;codecs=opus',
            'audio/webm',
            'audio/ogg;codecs=opus',
            'audio/ogg',
        ];
        this._mimeType = candidates.find(t => MediaRecorder.isTypeSupported(t)) || '';

        this._mediaRecorder = new MediaRecorder(
            this._stream,
            this._mimeType ? { mimeType: this._mimeType } : {}
        );

        this._mediaRecorder.ondataavailable = e => {
            if (e.data.size > 0) this._chunks.push(e.data);
        };

        this._mediaRecorder.start(100); // slice every 100 ms for smooth preview
        return this._stream;
    }

    /**
     * Stops recording and resolves with the final Blob.
     * @returns {Promise<Blob>}
     */
    stop() {
        return new Promise(resolve => {
            this._mediaRecorder.onstop = () => {
                this._blob = new Blob(this._chunks, {
                    type: this._mimeType || 'audio/webm',
                });
                this._releaseStream();
                resolve(this._blob);
            };
            this._mediaRecorder.stop();
        });
    }

    /**
     * Wraps the recorded blob as a File so it is compatible with handleFileUpload().
     * @param {string} [filename]
     * @returns {File|null}
     */
    getFile(filename) {
        if (!this._blob) return null;
        const ext = this._mimeType.includes('ogg') ? 'ogg' : 'webm';
        const name = filename || `recording_${Date.now()}.${ext}`;
        return new File([this._blob], name, { type: this._blob.type });
    }

    _releaseStream() {
        this._stream?.getTracks().forEach(t => t.stop());
        this._stream = null;
    }
}

window.AudioRecorder = AudioRecorder;
