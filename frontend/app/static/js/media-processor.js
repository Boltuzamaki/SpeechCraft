// Client-side audio extraction and media processing
class MediaProcessor {
    constructor() {
        this.ffmpeg = null;
        this.isLoaded = false;
        this.init();
    }

    async init() {
        try {
            // Load FFmpeg.wasm for client-side processing
            this.ffmpeg = FFmpeg.createFFmpeg({
                log: true,
                corePath: 'https://unpkg.com/@ffmpeg/core@0.11.0/dist/ffmpeg-core.js'
            });
            
            await this.ffmpeg.load();
            this.isLoaded = true;
            console.log('FFmpeg loaded successfully');
        } catch (error) {
            console.warn('FFmpeg failed to load, will use fallback method:', error);
            this.isLoaded = false;
        }
    }

    async extractAudio(file) {
        try {
            if (file.type.startsWith('audio/')) {
                // If it's already audio, just convert to standard format
                return await this.processAudioFile(file);
            } else if (file.type.startsWith('video/')) {
                // Extract audio from video
                return await this.extractAudioFromVideo(file);
            } else {
                throw new Error('Unsupported file type');
            }
        } catch (error) {
            console.error('Audio extraction failed:', error);
            throw error;
        }
    }

    async processAudioFile(file) {
        try {
            // Create audio element to get duration and basic info
            const audio = document.createElement('audio');
            const url = URL.createObjectURL(file);
            audio.src = url;
            
            return new Promise((resolve, reject) => {
                audio.addEventListener('loadedmetadata', async () => {
                    try {
                        const duration = audio.duration;
                        URL.revokeObjectURL(url);
                        
                        // Convert to base64 for API
                        const arrayBuffer = await file.arrayBuffer();
                        const base64 = this.arrayBufferToBase64(arrayBuffer);
                        
                        resolve({
                            audioData: base64,
                            duration: duration,
                            type: 'audio',
                            originalFile: file
                        });
                    } catch (error) {
                        reject(error);
                    }
                });
                
                audio.addEventListener('error', () => {
                    reject(new Error('Failed to load audio file'));
                });
            });
        } catch (error) {
            throw new Error('Audio processing failed: ' + error.message);
        }
    }

    async extractAudioFromVideo(file) {
        try {
            // Create video element to get duration and basic info
            const video = document.createElement('video');
            const url = URL.createObjectURL(file);
            video.src = url;
            
            return new Promise((resolve, reject) => {
                video.addEventListener('loadedmetadata', async () => {
                    try {
                        const duration = video.duration;
                        URL.revokeObjectURL(url);
                        
                        let audioData;
                        
                        if (this.isLoaded) {
                            // Use FFmpeg for extraction
                            audioData = await this.extractWithFFmpeg(file);
                        } else {
                            // Fallback: Use Web Audio API
                            audioData = await this.extractWithWebAudio(file);
                        }
                        
                        resolve({
                            audioData: audioData,
                            duration: duration,
                            type: 'video',
                            originalFile: file
                        });
                    } catch (error) {
                        reject(error);
                    }
                });
                
                video.addEventListener('error', () => {
                    reject(new Error('Failed to load video file'));
                });
            });
        } catch (error) {
            throw new Error('Video processing failed: ' + error.message);
        }
    }

    async extractWithFFmpeg(file) {
        try {
            const { name } = file;
            const inputName = `input.${name.split('.').pop()}`;
            const outputName = 'output.wav';
            
            // Write file to FFmpeg filesystem
            this.ffmpeg.FS('writeFile', inputName, new Uint8Array(await file.arrayBuffer()));
            
            // Extract audio
            await this.ffmpeg.run('-i', inputName, '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1', outputName);
            
            // Read output
            const data = this.ffmpeg.FS('readFile', outputName);
            
            // Clean up
            this.ffmpeg.FS('unlink', inputName);
            this.ffmpeg.FS('unlink', outputName);
            
            return this.arrayBufferToBase64(data.buffer);
        } catch (error) {
            console.error('FFmpeg extraction failed:', error);
            // Fallback to Web Audio API
            return await this.extractWithWebAudio(file);
        }
    }

    async extractWithWebAudio(file) {
        try {
            // This is a simplified fallback that works with some video formats
            // In production, you might want to use a more robust solution
            const video = document.createElement('video');
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            return new Promise((resolve, reject) => {
                video.addEventListener('loadeddata', async () => {
                    try {
                        // Create audio context
                        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                        const source = audioContext.createMediaElementSource(video);
                        const destination = audioContext.createMediaStreamDestination();
                        
                        source.connect(destination);
                        
                        // Record audio stream
                        const mediaRecorder = new MediaRecorder(destination.stream);
                        const chunks = [];
                        
                        mediaRecorder.ondataavailable = (event) => {
                            chunks.push(event.data);
                        };
                        
                        mediaRecorder.onstop = async () => {
                            const blob = new Blob(chunks, { type: 'audio/wav' });
                            const arrayBuffer = await blob.arrayBuffer();
                            resolve(this.arrayBufferToBase64(arrayBuffer));
                        };
                        
                        mediaRecorder.start();
                        video.play();
                        
                        // Stop recording when video ends
                        video.addEventListener('ended', () => {
                            mediaRecorder.stop();
                        });
                        
                    } catch (error) {
                        reject(error);
                    }
                });
                
                video.src = URL.createObjectURL(file);
                video.load();
            });
        } catch (error) {
            throw new Error('Web Audio extraction failed: ' + error.message);
        }
    }

    arrayBufferToBase64(buffer) {
        let binary = '';
        const bytes = new Uint8Array(buffer);
        for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return btoa(binary);
    }

    getFileInfo(file) {
        return {
            name: file.name,
            size: file.size,
            type: file.type,
            lastModified: file.lastModified
        };
    }
}

// Global media processor instance
window.mediaProcessor = new MediaProcessor();