/**
 * WaveformVisualizer : Single Responsibility: frequency-bar animation only.
 * Accepts a MediaStream and a <canvas> element; knows nothing about recording.
 */
class WaveformVisualizer {
    constructor(canvas) {
        this._canvas = canvas;
        this._ctx = canvas.getContext('2d');
        this._animationId = null;
        this._audioCtx = null;
        this._analyser = null;
    }

    /**
     * Connects the stream to the Web Audio analyser and begins drawing.
     * @param {MediaStream} stream
     */
    start(stream) {
        this._audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        this._analyser = this._audioCtx.createAnalyser();
        this._analyser.fftSize = 256;

        const source = this._audioCtx.createMediaStreamSource(stream);
        source.connect(this._analyser);

        this._render();
    }

    /** Stops animation and clears the canvas. */
    stop() {
        cancelAnimationFrame(this._animationId);
        this._animationId = null;
        this._audioCtx?.close();
        this._audioCtx = null;
        this._analyser = null;
        this._ctx.clearRect(0, 0, this._canvas.width, this._canvas.height);
    }

    _render() {
        const analyser = this._analyser;
        const ctx = this._ctx;
        const { width, height } = this._canvas;
        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        const barWidth = (width / bufferLength) * 2.5;

        const draw = () => {
            this._animationId = requestAnimationFrame(draw);
            analyser.getByteFrequencyData(dataArray);
            ctx.clearRect(0, 0, width, height);

            let x = 0;
            for (let i = 0; i < bufferLength; i++) {
                const barHeight = (dataArray[i] / 255) * height;
                const grad = ctx.createLinearGradient(0, height, 0, height - barHeight);
                grad.addColorStop(0, '#38BDF8');
                grad.addColorStop(1, '#818CF8');
                ctx.fillStyle = grad;
                ctx.fillRect(x, height - barHeight, barWidth - 1, barHeight);
                x += barWidth;
            }
        };

        draw();
    }
}

window.WaveformVisualizer = WaveformVisualizer;
