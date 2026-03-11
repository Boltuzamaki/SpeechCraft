class MediaPlayer {
    constructor(containerElement, jobData) {
        this.containerElement = containerElement;
        this.job = jobData;
        this.segments = (jobData.segments || []).map(seg => ({
            ...seg,
            start_time: parseFloat(seg.start_time),
            end_time: parseFloat(seg.end_time)
        }));
        this.currentSegment = null;
        this.isVideo = jobData.file_type === 'video';
        this.subtitleSettings = {
            fontSize: 16,
            fontColor: '#ffffff',
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            fontFamily: 'Arial, sans-serif',
            position: 'bottom'
        };

        this.isPlayingExpanded = false;
        this.ccEnabled = false;

        this.segmentsPerScroll = 1;
        this.lastScrolledBatchIndex = -1;

        this.media = null;
        this.playPauseIcon = null;
        this.timelineProgress = null;
        this.timelineTrack = null;
        this.timelineSegmentsContainer = null;
        this.currentTimeSpan = null;
        this.totalTimeSpan = null;
        this.subtitleOverlay = null;
        this.subtitleText = null;
        this.volumeSlider = null;
        this.playPauseBtn = null;
        this.toggleSubtitlesBtn = null;
        this.previousSegmentBtn = null;
        this.nextSegmentBtn = null;
        this.showSubtitleSettingsBtn = null;
        this.showEmbedOptionsBtn = null;
        this.toggleFullscreenBtn = null;

        this.init();
    }

    init() {
        this.createPlayer();
        this.bindEvents();
        this.loadSubtitles();
        this.updateTotalTime();
        this.createSegmentMarkers();
        this.applySubtitleStyles();
    }

    createPlayer() {
        const playerHTML = `
            <div class="modern-media-player glass-effect">
                <div class="player-header">
                    <h5 class="text-white mb-0 ">${this.job.filename}</h5>
                    <div class="player-controls-header">
                        <button class="btn btn-sm btn-outline-light" id="toggleSubtitlesBtn">
                            <i class="fas fa-closed-captioning"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-light" id="showSubtitleSettingsBtn">
                            <i class="fas fa-cog"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-light" id="showEmbedOptionsBtn">
                            <i class="fas fa-download"></i> Embed SRT
                        </button>
                    </div>
                </div>
                
                <div class="player-container" style="position: relative; width: 100%;">
                    ${this.isVideo ? this.createVideoPlayer() : this.createAudioPlayer()}
                    <div class="subtitle-overlay" id="subtitleOverlay" style="display: none; position: absolute; bottom: 8%; left: 50%; transform: translateX(-50%); width: max-content; max-width: 90%; text-align: center; pointer-events: none; z-index: 100;">
                        <div class="subtitle-text" id="subtitleText" style="display: inline-block; padding: 4px 8px; border-radius: 4px; white-space: pre-wrap;"></div>
                    </div>
                </div>
                
                <div class="player-timeline">
                    <div class="timeline-track" id="timelineTrack">
                        <div class="timeline-progress" id="timelineProgress"></div>
                        <div class="timeline-segments" id="timelineSegments"></div>
                    </div>
                    <div class="time-display">
                        <span id="currentTime">0:00</span> / <span id="totalTime">0:00</span>
                    </div>
                </div>
                
                <div class="player-controls">
                    <button class="btn btn-light" id="playPauseBtn">
                        <i class="fas fa-play" id="playPauseIcon"></i>
                    </button>
                    <button class="btn btn-outline-light" id="previousSegmentBtn">
                        <i class="fas fa-step-backward"></i>
                    </button>
                    <button class="btn btn-outline-light" id="nextSegmentBtn">
                        <i class="fas fa-step-forward"></i>
                    </button>
                    <div class="volume-control">
                        <i class="fas fa-volume-up text-light"></i>
                        <input type="range" class="volume-slider" min="0" max="1" step="0.1" value="1" 
                               id="volumeSlider">
                    </div>
                    <button class="btn btn-outline-light" id="toggleFullscreenBtn">
                        <i class="fas fa-expand"></i>
                    </button>
                </div>
            </div>
        `;
        
        this.containerElement.innerHTML = playerHTML;

        this.media = this.containerElement.querySelector('#mediaElement');
        this.playPauseIcon = this.containerElement.querySelector('#playPauseIcon');
        this.timelineProgress = this.containerElement.querySelector('#timelineProgress');
        this.timelineTrack = this.containerElement.querySelector('#timelineTrack');
        this.timelineSegmentsContainer = this.containerElement.querySelector('#timelineSegments');
        this.currentTimeSpan = this.containerElement.querySelector('#currentTime');
        this.totalTimeSpan = this.containerElement.querySelector('#totalTime');
        this.subtitleOverlay = this.containerElement.querySelector('#subtitleOverlay');
        this.subtitleText = this.containerElement.querySelector('#subtitleText');
        this.volumeSlider = this.containerElement.querySelector('#volumeSlider');
        
        this.playPauseBtn = this.containerElement.querySelector('#playPauseBtn');
        this.previousSegmentBtn = this.containerElement.querySelector('#previousSegmentBtn');
        this.nextSegmentBtn = this.containerElement.querySelector('#nextSegmentBtn');
        this.toggleSubtitlesBtn = this.containerElement.querySelector('#toggleSubtitlesBtn');
        this.showSubtitleSettingsBtn = this.containerElement.querySelector('#showSubtitleSettingsBtn');
        this.showEmbedOptionsBtn = this.containerElement.querySelector('#showEmbedOptionsBtn');
        this.toggleFullscreenBtn = this.containerElement.querySelector('#toggleFullscreenBtn');
    }

    createVideoPlayer() {
        return `
            <video
                id="mediaElement"
                class="media-element"
                preload="metadata"
                style="width: 100%; display: block;"
            >
                <source src="${this.job.original_file_url}" type="${this.getVideoMimeType()}">
                Your browser does not support the video tag.
            </video>
        `;
    }

    createAudioPlayer() {
        return `
            <div class="audio-visualizer">
                <canvas id="audioCanvas" width="800" height="200"></canvas>
                <audio
                    id="mediaElement"
                    class="media-element"
                    preload="metadata"
                >
                    <source src="${this.job.original_file_url || this.job.audio_file_url}" type="${this.getAudioMimeType()}">
                    Your browser does not support the audio tag.
                </audio>
            </div>
        `;
    }

    bindEvents() {
        if (!this.media) {
            console.error("Media element not found. Cannot bind events.");
            return;
        }

        this.media.addEventListener('loadedmetadata', () => {
            if (this.media.duration === Infinity) {
                // WebM files from recorder report Infinity until seeked — force resolution
                const resolveInfinity = () => {
                    if (isFinite(this.media.duration)) {
                        this.media.removeEventListener('durationchange', resolveInfinity);
                        this.media.currentTime = 0;
                        this.updateTotalTime();
                        this.createSegmentMarkers();
                    }
                };
                this.media.addEventListener('durationchange', resolveInfinity);
                this.media.currentTime = 1e101; // seek far ahead to trigger duration resolution
            } else {
                this.updateTotalTime();
                this.createSegmentMarkers();
            }
        });

        this.media.addEventListener('timeupdate', () => {
            this.updateProgress();
            this.updateCurrentSegment();
            this.updateSubtitles();
        });

        this.media.addEventListener('play', () => {
            if (!this.isPlayingExpanded) {
                this.toggleTranscriptExpansionMode(true);
            }
            this.playPauseIcon.className = 'fas fa-pause';
        });

        this.media.addEventListener('ended', () => {
            this.playPauseIcon.className = 'fas fa-play';
            this.toggleTranscriptExpansionMode(false);
            this.lastScrolledBatchIndex = -1;
        });

        this.media.addEventListener('pause', () => {
             this.playPauseIcon.className = 'fas fa-play';
        });

        if (this.playPauseBtn) this.playPauseBtn.addEventListener('click', () => this.togglePlay());
        if (this.previousSegmentBtn) this.previousSegmentBtn.addEventListener('click', () => this.previousSegment());
        if (this.nextSegmentBtn) this.nextSegmentBtn.addEventListener('click', () => this.nextSegment());
        if (this.volumeSlider) this.volumeSlider.addEventListener('input', (e) => this.setVolume(e.target.value));
        if (this.toggleSubtitlesBtn) this.toggleSubtitlesBtn.addEventListener('click', () => this.toggleSubtitles());
        if (this.showSubtitleSettingsBtn) this.showSubtitleSettingsBtn.addEventListener('click', () => this.showSubtitleSettings());
        if (this.showEmbedOptionsBtn) this.showEmbedOptionsBtn.addEventListener('click', () => this.showEmbedOptions());
        if (this.toggleFullscreenBtn) this.toggleFullscreenBtn.addEventListener('click', () => this.toggleFullscreen());

        if (this.timelineTrack) {
            this.timelineTrack.addEventListener('click', (e) => {
                const rect = this.timelineTrack.getBoundingClientRect();
                const percent = (e.clientX - rect.left) / rect.width;
                if (!isNaN(this.media.duration) && this.media.duration > 0) {
                    this.media.currentTime = percent * this.media.duration;
                    const targetSegment = this.segments.find(s => this.media.currentTime >= s.start_time && s.end_time > s.start_time && this.media.currentTime < s.end_time);
                    if(targetSegment) {
                         const segmentIndex = this.segments.findIndex(s => s.id === targetSegment.id);
                         this.lastScrolledBatchIndex = Math.floor(segmentIndex / this.segmentsPerScroll) - 1;
                    }
                }
            });
        }
    }

    toggleTranscriptExpansionMode(enable) {
        if (this.isVideo) return;

        const mainContentView = document.getElementById('mainContentView');
        const rowElement = document.querySelector('.container-fluid > .row');

        if (!mainContentView || !rowElement) return;

        if (enable) {
            mainContentView.classList.add('transcript-expanded-mode');
            rowElement.classList.add('transcript-expanded-mode');
            this.isPlayingExpanded = true;
        } else {
            mainContentView.classList.remove('transcript-expanded-mode');
            rowElement.classList.remove('transcript-expanded-mode');
            this.isPlayingExpanded = false;
        }
        
        if (this.currentSegment) {
            setTimeout(() => this.highlightSegment(this.currentSegment), 50);
        }
    }

    loadSubtitles() {
        if (!this.segments.length || !this.media) return;
        this.createVTTTrack();
    }

    createVTTTrack() {
        let vttContent = 'WEBVTT\n\n';
        
        this.segments.forEach((segment, index) => {
            const startTime = this.formatTimeVTT(segment.start_time);
            const endTime = this.formatTimeVTT(segment.end_time);
            const text = segment.edited_text || segment.original_text;
            
            vttContent += `${index + 1}\n`;
            vttContent += `${startTime} --> ${endTime}\n`;
            vttContent += `${text}\n\n`;
        });

        const blob = new Blob([vttContent], { type: 'text/vtt' });
        const url = URL.createObjectURL(blob);
        
        const track = document.createElement('track');
        track.kind = 'subtitles';
        track.label = 'English';
        track.srclang = 'en';
        track.src = url;
        track.default = false;

        this.media.appendChild(track);
        track.addEventListener('load', () => {
            if (this.media.textTracks && this.media.textTracks.length > 0) {
                this.media.textTracks[0].mode = 'hidden';
            }
        });
    }

    createSegmentMarkers() {
        if (!this.timelineSegmentsContainer || !this.media || isNaN(this.media.duration)) {
             this.media.addEventListener('loadedmetadata', () => this.createSegmentMarkers(), { once: true });
             return;
        }

        this.timelineSegmentsContainer.innerHTML = '';
        
        const duration = this.media.duration;
        this.segments.forEach((segment, index) => {
            const marker = document.createElement('div');
            marker.className = 'segment-marker';
            marker.style.left = `${(segment.start_time / duration) * 100}%`;
            marker.title = `Segment ${index + 1}: ${this.formatTime(segment.start_time)} - ${this.formatTime(segment.end_time)}`;
            marker.addEventListener('click', (e) => {
                e.stopPropagation();
                this.seekToSegment(segment);
            });
            
            this.timelineSegmentsContainer.appendChild(marker);
        });
    }

    updateProgress() {
        if (!this.media || isNaN(this.media.duration)) return;
        const progress = (this.media.currentTime / this.media.duration) * 100;
        this.timelineProgress.style.width = `${progress}%`;
        this.currentTimeSpan.textContent = this.formatTime(this.media.currentTime);
    }

    updateCurrentSegment() {
        const currentTime = this.media.currentTime;
        const segment = this.segments.find(s => 
            currentTime >= s.start_time && currentTime < s.end_time
        );
        
        if (segment && segment !== this.currentSegment) {
            this.currentSegment = segment;
            this.highlightSegment(segment);
            this.updateSubtitles();
        } else if (!segment && this.currentSegment) {
            this.currentSegment = null;
            this.highlightSegment(null);
            this.updateSubtitles();
        }
    }

    updateSubtitles() {
        if (!this.subtitleOverlay || !this.subtitleText) return;

        if (this.ccEnabled && this.currentSegment) {
            const text = this.currentSegment.edited_text || this.currentSegment.original_text;
            if (text && text.trim()) {
                this.subtitleText.innerHTML = text;
                this.subtitleOverlay.style.display = 'block';
                return;
            }
        }

        this.subtitleOverlay.style.display = 'none';
        this.subtitleText.textContent = '';
    }

    highlightSegment(segment) {
        document.querySelectorAll('.transcript-timeline .timeline-segment.active').forEach(el => {
            el.classList.remove('active');
        });

        if (segment) {
            const segmentElement = document.querySelector(`.transcript-timeline .timeline-segment[data-segment-id="${segment.id}"]`);
            const container = document.querySelector('.transcript-timeline .timeline-container'); 

            if (segmentElement && container) {
                segmentElement.classList.add('active');
                const segmentIndex = this.segments.findIndex(s => s.id === segment.id);
                const currentBatchIndex = Math.floor(segmentIndex / this.segmentsPerScroll);

                if (currentBatchIndex > this.lastScrolledBatchIndex) {
                    const firstSegmentOfBatchIndex = currentBatchIndex * this.segmentsPerScroll;
                    const firstSegmentOfBatch = this.segments[firstSegmentOfBatchIndex];

                    if (firstSegmentOfBatch) {
                        const targetSegmentElement = document.querySelector(`.transcript-timeline .timeline-segment[data-segment-id="${firstSegmentOfBatch.id}"]`);
                        if (targetSegmentElement) {
                            const scrollPaddingTop = container.clientHeight * 0.15;
                            let scrollToPosition = targetSegmentElement.offsetTop - scrollPaddingTop;
                            const maxScrollTop = container.scrollHeight - container.clientHeight;
                            scrollToPosition = Math.max(0, Math.min(scrollToPosition, maxScrollTop));

                            container.scrollTo({
                                top: scrollToPosition,
                                behavior: 'smooth'
                            });
                            this.lastScrolledBatchIndex = currentBatchIndex;
                        }
                    }
                }
            }
        } else {
            this.lastScrolledBatchIndex = -1;
        }
    }

    togglePlay() {
        if (this.media.paused) {
            this.media.play();
        } else {
            this.media.pause();
        }
    }

    toggleSubtitles() {
        if (!this.toggleSubtitlesBtn) return;

        this.ccEnabled = !this.ccEnabled;

        if (this.ccEnabled) {
            this.toggleSubtitlesBtn.classList.remove('btn-outline-light');
            this.toggleSubtitlesBtn.classList.add('btn-light');
        } else {
            this.toggleSubtitlesBtn.classList.remove('btn-light');
            this.toggleSubtitlesBtn.classList.add('btn-outline-light');
            if (this.subtitleOverlay) this.subtitleOverlay.style.display = 'none';
        }

        if (this.ccEnabled && this.media) {
            const currentTime = this.media.currentTime;
            this.currentSegment = this.segments.find(
                s => currentTime >= s.start_time && currentTime < s.end_time
            ) || null;
        }
        this.updateSubtitles();
    }

    seekToSegment(segment) {
        if (this.media && typeof segment.start_time === 'number') {
            this.media.currentTime = segment.start_time;
            if (this.media.paused && (!window.transcriptEditor || !window.transcriptEditor.isEditMode)) {
                this.media.play();
            }
            const segmentIndex = this.segments.findIndex(s => s.id === segment.id);
            this.lastScrolledBatchIndex = Math.floor(segmentIndex / this.segmentsPerScroll) - 1;
            this.highlightSegment(segment);
        }
    }

    previousSegment() {
        if (!this.currentSegment) return;
        const currentIndex = this.segments.findIndex(s => s.id === this.currentSegment.id);
        if (currentIndex > 0) {
            this.seekToSegment(this.segments[currentIndex - 1]);
        }
    }

    nextSegment() {
        if (!this.currentSegment) return;
        const currentIndex = this.segments.findIndex(s => s.id === this.currentSegment.id);
        if (currentIndex < this.segments.length - 1) {
            this.seekToSegment(this.segments[currentIndex + 1]);
        }
    }

    setVolume(value) {
        if (this.media) {
            this.media.volume = value;
        }
    }

    toggleFullscreen() {
        const playerContainer = this.containerElement.querySelector('.player-container');
        
        if (this.isVideo && playerContainer) {
            if (document.fullscreenElement) {
                if (document.exitFullscreen) document.exitFullscreen();
            } else if (playerContainer.requestFullscreen) {
                playerContainer.requestFullscreen();
            } else if (this.media.requestFullscreen) {
                this.media.requestFullscreen();
            }
        }
    }

    showSubtitleSettings() {
        this.createSubtitleSettingsModal();
    }

    createSubtitleSettingsModal() {
        const modalHTML = `
            <div class="modal fade" id="subtitleSettingsModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content glass-effect">
                        <div class="modal-header border-0">
                            <h5 class="modal-title text-white">Subtitle Settings</h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="mb-3">
                                <label class="form-label text-light">Font Size</label>
                                <input type="range" class="form-range" min="12" max="24" value="${this.subtitleSettings.fontSize}" 
                                       oninput="document.getElementById('fontSizeVal').textContent = this.value + 'px'; mediaPlayer.updateSubtitleSetting('fontSize', this.value)">
                                <small class="text-light" id="fontSizeVal">${this.subtitleSettings.fontSize}px</small>
                            </div>
                            
                            <div class="mb-3">
                                <label class="form-label text-light">Font Color</label>
                                <input type="color" class="form-control" value="${this.subtitleSettings.fontColor}" 
                                       onchange="mediaPlayer.updateSubtitleSetting('fontColor', this.value)">
                            </div>
                            
                            <div class="mb-3">
                                <label class="form-label text-light">Background Color</label>
                                <input type="color" class="form-control" value="${this.subtitleSettings.backgroundColor.replace('rgba(0, 0, 0, 0.8)', '#000000')}" 
                                       onchange="mediaPlayer.updateSubtitleSetting('backgroundColor', this.value)">
                            </div>
                            
                            <div class="mb-3">
                                <label class="form-label text-light">Font Family</label>
                                <select class="form-select" onchange="mediaPlayer.updateSubtitleSetting('fontFamily', this.value)">
                                    <option value="Arial, sans-serif" ${this.subtitleSettings.fontFamily === 'Arial, sans-serif' ? 'selected' : ''}>Arial</option>
                                    <option value="Georgia, serif" ${this.subtitleSettings.fontFamily === 'Georgia, serif' ? 'selected' : ''}>Georgia</option>
                                    <option value="'Times New Roman', serif" ${this.subtitleSettings.fontFamily === "'Times New Roman', serif" ? 'selected' : ''}>Times New Roman</option>
                                    <option value="'Courier New', monospace" ${this.subtitleSettings.fontFamily === "'Courier New', monospace" ? 'selected' : ''}>Courier New</option>
                                </select>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        const existing = document.getElementById('subtitleSettingsModal');
        if (existing) existing.remove();
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        new bootstrap.Modal(document.getElementById('subtitleSettingsModal')).show();
    }

    updateSubtitleSetting(property, value) {
        this.subtitleSettings[property] = value;
        this.applySubtitleStyles();
    }

    applySubtitleStyles() {
        if (this.subtitleText) {
            this.subtitleText.style.fontSize = `${this.subtitleSettings.fontSize}px`;
            this.subtitleText.style.color = this.subtitleSettings.fontColor;
            this.subtitleText.style.backgroundColor = this.subtitleSettings.backgroundColor;
            this.subtitleText.style.fontFamily = this.subtitleSettings.fontFamily;
        }
    }

    showEmbedOptions() {
        this.createEmbedModal();
    }

    createEmbedModal() {
        const modalHTML = `
            <div class="modal fade" id="embedModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content glass-effect">
                        <div class="modal-header border-0">
                            <h5 class="modal-title text-white">Embed Subtitles in Video</h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="alert alert-info">
                                <i class="fas fa-info-circle me-2"></i>
                                This will create a new video file with embedded subtitles. The process may take a few minutes.
                            </div>
                            
                            <div class="mb-3">
                                <label class="form-label text-light">Subtitle Position</label>
                                <select class="form-select" id="subtitlePosition">
                                    <option value="bottom">Bottom</option>
                                    <option value="top">Top</option>
                                    <option value="center">Center</option>
                                </select>
                            </div>
                            
                            <div class="mb-3">
                                <label class="form-label text-light">Font Size</label>
                                <input type="range" class="form-range" min="16" max="48" value="24" id="embedFontSize"
                                       oninput="document.getElementById('embedFontSizeVal').textContent = this.value + 'px';">
                                <small class="text-light" id="embedFontSizeVal">24px</small>
                            </div>
                            
                            <div class="mb-3">
                                <label class="form-label text-light">Font Color</label>
                                <input type="color" class="form-control" value="#ffffff" id="embedFontColor">
                            </div>
                            
                            <div class="mb-3">
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" id="embedOutline" checked>
                                    <label class="form-check-label text-light" for="embedOutline">
                                        Add text outline (recommended)
                                    </label>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer border-0">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" onclick="mediaPlayer.embedSubtitles()">
                                <i class="fas fa-video me-2"></i>Embed Subtitles
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        const existing = document.getElementById('embedModal');
        if (existing) existing.remove();
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        new bootstrap.Modal(document.getElementById('embedModal')).show();
    }

    async embedSubtitles() {
        showToast('Subtitle embedding started. You will be notified when complete.', 'info');
        
        const settings = {
            position: document.getElementById('subtitlePosition').value,
            fontSize: document.getElementById('embedFontSize').value,
            fontColor: document.getElementById('embedFontColor').value,
            outline: document.getElementById('embedOutline').checked
        };
        
        try {
            const response = await fetch('/embed_subtitles', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    job_id: this.job.id,
                    settings: settings
                })
            });
            
            const result = await response.json();
            if (result.success) {
                showToast('Subtitle embedding completed! Downloading...', 'success');
                const a = document.createElement('a');
                a.href = result.embedded_url;
                a.download = 'embedded_' + (this.job.filename || 'video.mp4');
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
            } else {
                showToast('Embedding failed: ' + result.error, 'error');
            }
        } catch (error) {
            showToast('Network error during embedding', 'error');
        }
        
        bootstrap.Modal.getInstance(document.getElementById('embedModal')).hide();
    }

    updateTotalTime() {
        if (!this.media) return;
        const dur = this.media.duration;
        if (isFinite(dur) && dur > 0) {
            this.totalTimeSpan.textContent = this.formatTime(dur);
        } else if (this.segments.length > 0) {
            // Fallback: use last segment end_time (e.g. while WebM duration resolves)
            const lastEnd = Math.max(...this.segments.map(s => s.end_time));
            this.totalTimeSpan.textContent = this.formatTime(lastEnd);
        }
    }

    formatTime(seconds) {
        if (!isFinite(seconds) || isNaN(seconds) || seconds < 0) return '0:00';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    formatTimeVTT(seconds) {
        const hours = Math.floor(seconds / 3600);
        const mins = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        const ms = Math.floor((seconds % 1) * 1000);
        
        return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${ms.toString().padStart(3, '0')}`;
    }

    getVideoMimeType() {
        const extension = this.job.filename.split('.').pop().toLowerCase();
        const mimeTypes = {
            'mp4': 'video/mp4',
            'webm': 'video/webm',
            'ogg': 'video/ogg',
            'avi': 'video/x-msvideo',
            'mov': 'video/quicktime'
        };
        return mimeTypes[extension] || 'video/mp4';
    }

    getAudioMimeType() {
        const extension = this.job.filename.split('.').pop().toLowerCase();
        const mimeTypes = {
            'mp3': 'audio/mpeg',
            'wav': 'audio/wav',
            'ogg': 'audio/ogg',
            'flac': 'audio/flac',
            'm4a': 'audio/mp4',
            'webm': 'audio/webm'
        };
        return mimeTypes[extension] || 'audio/mpeg';
    }
}

window.mediaPlayer = null;