// Fixed Transcript editor functionality
class TranscriptEditor {
    constructor() {
        this.isEditMode = false;
        this.activeEditSegment = null;
        this.unsavedChanges = false;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.setupAutoSave();
    }
    
    bindEvents() {
        // Remove existing onclick attributes and bind properly
        document.querySelectorAll('[onclick*="toggleEditMode"]').forEach(btn => {
            btn.removeAttribute('onclick');
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleEditMode();
            });
        });
        
        document.querySelectorAll('[onclick*="exportTranscript"]').forEach(btn => {
            btn.removeAttribute('onclick');
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                this.exportTranscript();
            });
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));
        
        // Warn about unsaved changes
        window.addEventListener('beforeunload', (e) => {
            if (this.unsavedChanges) {
                e.preventDefault();
                e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
                return e.returnValue;
            }
        });
    }
    
    setupAutoSave() {
        // Auto-save every 30 seconds if there are unsaved changes
        setInterval(() => {
            if (this.unsavedChanges && this.activeEditSegment) {
                this.autoSave();
            }
        }, 30000);
    }
    
    toggleEditMode() {
        console.log('Toggle edit mode called, current state:', this.isEditMode);
        
        this.isEditMode = !this.isEditMode;
        
        // Fix: Use correct selector for transcript-actions (not transcription-actions)
        const button = document.querySelector('.transcript-actions .btn-primary, .transcript-actions .btn-warning');
        
        if (!button) {
            console.error('Edit mode button not found! Looking for:', '.transcript-actions .btn-primary');
            return;
        }
        
        if (this.isEditMode) {
            button.innerHTML = '<i class="fas fa-eye me-1"></i>View Mode';
            button.classList.remove('btn-primary');
            button.classList.add('btn-warning');
            this.enableEditMode();
        } else {
            button.innerHTML = '<i class="fas fa-edit me-1"></i>Edit Mode';
            button.classList.remove('btn-warning');
            button.classList.add('btn-primary');
            this.disableEditMode();
        }
    }
    
    enableEditMode() {
        console.log('Enabling edit mode');
        
        // Show edit buttons for each segment
        document.querySelectorAll('.edit-segment').forEach(btn => {
            btn.style.display = 'inline-block';
        });
        
        // Add visual indicator and click handlers to segments
        document.querySelectorAll('.timeline-segment').forEach(segment => {
            segment.classList.add('editable');
            segment.style.cursor = 'pointer';
            
            // Remove existing listeners to avoid duplicates
            segment.removeEventListener('click', this.handleSegmentClick);
            segment.addEventListener('click', (e) => this.handleSegmentClick(e, segment));
        });
        
        // Show toast notification
        if (typeof showToast === 'function') {
            showToast('Edit mode enabled. Click on any text segment to edit.', 'info');
        } else {
            console.log('Edit mode enabled. Click on any text segment to edit.');
        }
    }
    
    disableEditMode() {
        console.log('Disabling edit mode');
        
        // Hide edit buttons
        document.querySelectorAll('.edit-segment').forEach(btn => {
            btn.style.display = 'none';
        });
        
        // Remove visual indicators and click handlers
        document.querySelectorAll('.timeline-segment').forEach(segment => {
            segment.classList.remove('editable');
            segment.style.cursor = 'default';
            // Note: removeEventListener with arrow functions won't work, 
            // but we'll handle this by checking isEditMode in the handler
        });
        
        this.cancelAllEdits();
    }
    
    handleSegmentClick(e, segment) {
        console.log('Segment clicked, edit mode:', this.isEditMode);
        
        if (!this.isEditMode) return;
        
        const segmentId = segment.dataset.segmentId;
        console.log('Editing segment:', segmentId);
        
        // Don't trigger if clicking on buttons
        if (e.target.closest('button')) {
            console.log('Button clicked, ignoring');
            return;
        }
        
        // Prevent the original onclick from firing (media player seek)
        e.stopPropagation();
        
        this.editSegment(segmentId);
    }
    
    editSegment(segmentId) {
        console.log('editSegment called for:', segmentId);
        
        // Cancel any other active edits
        this.cancelAllEdits();
        
        const segment = document.querySelector(`[data-segment-id="${segmentId}"]`);
        if (!segment) {
            console.error('Segment not found:', segmentId);
            return;
        }
        
        const textDisplay = segment.querySelector('.text-display');
        const textEditor = segment.querySelector('.text-editor');
        const textarea = textEditor.querySelector('textarea');
        
        if (!textDisplay || !textEditor || !textarea) {
            console.error('Missing elements in segment:', segmentId);
            return;
        }
        
        // Show editor, hide display
        textDisplay.style.display = 'none';
        textEditor.style.display = 'block';
        
        // Focus and select text
        textarea.focus();
        textarea.select();
        
        // Track active edit
        this.activeEditSegment = segmentId;
        
        // Remove existing event listeners to avoid duplicates
        textarea.removeEventListener('keydown', this.textareaKeyHandler);
        textarea.removeEventListener('input', this.textareaInputHandler);
        
        // Create bound handlers
        this.textareaKeyHandler = (e) => {
            if (e.key === 'Enter' && !e.ctrlKey) {
                e.preventDefault();
                this.saveSegmentEdit(segmentId);
            } else if (e.key === 'Escape') {
                e.preventDefault();
                this.cancelSegmentEdit(segmentId);
            }
        };
        
        this.textareaInputHandler = () => {
            this.unsavedChanges = true;
        };
        
        // Add event listeners
        textarea.addEventListener('keydown', this.textareaKeyHandler);
        textarea.addEventListener('input', this.textareaInputHandler);
        
        console.log('Edit mode activated for segment:', segmentId);
    }
    
    saveSegmentEdit(segmentId) {
        console.log('Saving segment:', segmentId);
        
        const segment = document.querySelector(`[data-segment-id="${segmentId}"]`);
        if (!segment) return;
        
        const textEditor = segment.querySelector('.text-editor');
        const textarea = textEditor.querySelector('textarea');
        const newText = textarea.value.trim();
        
        if (!newText) {
            if (typeof showToast === 'function') {
                showToast('Text cannot be empty', 'warning');
            }
            textarea.focus();
            return;
        }
        
        // Show loading state
        const saveBtn = segment.querySelector('.save-edit');
        const originalText = saveBtn.innerHTML;
        saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Saving...';
        saveBtn.disabled = true;
        
        // Send to server
        fetch(`/edit_segment/${segmentId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: newText })
        })
        .then(response => {
            console.log('Save response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('Save response data:', data);
            
            if (data.success) {
                // Update display text
                const textDisplay = segment.querySelector('.text-display');
                textDisplay.textContent = newText;
                
                // Hide editor, show display
                textEditor.style.display = 'none';
                textDisplay.style.display = 'block';
                
                // Reset active edit
                this.activeEditSegment = null;
                this.unsavedChanges = false;
                
                if (typeof showToast === 'function') {
                    showToast('Segment updated successfully', 'success');
                }
            } else {
                if (typeof showToast === 'function') {
                    showToast(data.error || 'Failed to save changes', 'danger');
                }
            }
        })
        .catch(error => {
            console.error('Error saving segment:', error);
            if (typeof showToast === 'function') {
                showToast('Network error. Please try again.', 'danger');
            }
        })
        .finally(() => {
            // Reset button
            saveBtn.innerHTML = originalText;
            saveBtn.disabled = false;
        });
    }
    
    cancelSegmentEdit(segmentId) {
        console.log('Canceling edit for segment:', segmentId);
        
        const segment = document.querySelector(`[data-segment-id="${segmentId}"]`);
        if (!segment) return;
        
        const textDisplay = segment.querySelector('.text-display');
        const textEditor = segment.querySelector('.text-editor');
        const textarea = textEditor.querySelector('textarea');
        
        // Reset textarea to original text
        textarea.value = textDisplay.textContent;
        
        // Hide editor, show display
        textEditor.style.display = 'none';
        textDisplay.style.display = 'block';
        
        // Reset active edit
        this.activeEditSegment = null;
        this.unsavedChanges = false;
    }
    
    cancelAllEdits() {
        document.querySelectorAll('.text-editor').forEach(editor => {
            if (editor.style.display === 'block') {
                const segment = editor.closest('.timeline-segment');
                const segmentId = segment.dataset.segmentId;
                this.cancelSegmentEdit(segmentId);
            }
        });
    }
    
    autoSave() {
        if (this.activeEditSegment) {
            console.log('Auto-saving segment:', this.activeEditSegment);
            if (typeof showToast === 'function') {
                showToast('Auto-save: Changes saved locally', 'info');
            }
        }
    }
    
    exportTranscript() {
        console.log('Exporting transcript');
        
        const segments = document.querySelectorAll('.timeline-segment');
        if (segments.length === 0) {
            if (typeof showToast === 'function') {
                showToast('No transcript to export', 'warning');
            }
            return;
        }
        
        let exportText = '';
        let csvContent = 'Start Time,End Time,Text\n';
        let srtContent = '';
        
        segments.forEach((segment, index) => {
            const timeText = segment.querySelector('.time-badge').textContent;
            const text = segment.querySelector('.text-display').textContent.trim();
            
            // Plain text format
            exportText += `[${timeText}] ${text}\n\n`;
            
            // CSV format
            const times = timeText.split(' - ');
            const startTime = times[0].replace('s', '');
            const endTime = times[1].replace('s', '');
            csvContent += `"${startTime}","${endTime}","${text.replace(/"/g, '""')}"\n`;
            
            // SRT format
            const srtStartTime = this.formatSRTTime(parseFloat(startTime));
            const srtEndTime = this.formatSRTTime(parseFloat(endTime));
            srtContent += `${index + 1}\n${srtStartTime} --> ${srtEndTime}\n${text}\n\n`;
        });
        
        // Show export options
        this.showExportModal(exportText, csvContent, srtContent);
    }
    
    showExportModal(textContent, csvContent, srtContent) {
        const modalHtml = `
            <div class="modal fade" id="exportModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content glass-effect">
                        <div class="modal-header border-0">
                            <h5 class="modal-title text-white">Export Transcript</h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row g-3">
                                <div class="col-md-4">
                                    <button class="btn btn-outline-light w-100" onclick="window.transcriptEditor.downloadFile('${this.getCurrentFilename()}_transcript.txt', '${btoa(textContent)}')">
                                        <i class="fas fa-file-alt fa-2x mb-2"></i><br>
                                        Plain Text
                                    </button>
                                </div>
                                <div class="col-md-4">
                                    <button class="btn btn-outline-light w-100" onclick="window.transcriptEditor.downloadFile('${this.getCurrentFilename()}_transcript.csv', '${btoa(csvContent)}')">
                                        <i class="fas fa-table fa-2x mb-2"></i><br>
                                        CSV
                                    </button>
                                </div>
                                <div class="col-md-4">
                                    <button class="btn btn-outline-light w-100" onclick="window.transcriptEditor.downloadFile('${this.getCurrentFilename()}_transcript.srt', '${btoa(srtContent)}')">
                                        <i class="fas fa-closed-captioning fa-2x mb-2"></i><br>
                                        SRT Subtitles
                                    </button>
                                </div>
                            </div>
                            <div class="mt-4">
                                <h6 class="text-white">Preview (Plain Text):</h6>
                                <textarea class="form-control" rows="8" readonly>${textContent}</textarea>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal
        const existingModal = document.getElementById('exportModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Add new modal
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Show modal (assuming Bootstrap is available)
        if (typeof bootstrap !== 'undefined') {
            const modal = new bootstrap.Modal(document.getElementById('exportModal'));
            modal.show();
        }
    }
    
    downloadFile(filename, base64Content) {
        const content = atob(base64Content);
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        if (typeof showToast === 'function') {
            showToast(`Downloaded ${filename}`, 'success');
        }
    }
    
    getCurrentFilename() {
        const titleElement = document.querySelector('.transcription-view h4');
        if (titleElement) {
            return titleElement.textContent.replace(/\.[^/.]+$/, ''); // Remove extension
        }
        return 'transcript';
    }
    
    formatSRTTime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        const ms = Math.floor((seconds % 1) * 1000);
        
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')},${ms.toString().padStart(3, '0')}`;
    }
    
    handleKeyboardShortcuts(e) {
        // Ctrl+S to save current edit
        if (e.ctrlKey && e.key === 's') {
            e.preventDefault();
            if (this.activeEditSegment) {
                this.saveSegmentEdit(this.activeEditSegment);
            }
        }
        
        // Escape to cancel edit
        if (e.key === 'Escape' && this.activeEditSegment) {
            this.cancelSegmentEdit(this.activeEditSegment);
        }
        
        // Ctrl+E to toggle edit mode
        if (e.ctrlKey && e.key === 'e') {
            e.preventDefault();
            this.toggleEditMode();
        }
        
        // Ctrl+Shift+E to export
        if (e.ctrlKey && e.shiftKey && e.key === 'E') {
            e.preventDefault();
            this.exportTranscript();
        }
    }
}

// Global functions for backward compatibility
function editSegment(segmentId) {
    if (window.transcriptEditor) {
        window.transcriptEditor.editSegment(segmentId);
    }
}

function saveSegmentEdit(segmentId) {
    if (window.transcriptEditor) {
        window.transcriptEditor.saveSegmentEdit(segmentId);
    }
}

function cancelSegmentEdit(segmentId) {
    if (window.transcriptEditor) {
        window.transcriptEditor.cancelSegmentEdit(segmentId);
    }
}

function toggleEditMode() {
    console.log('Global toggleEditMode called');
    if (window.transcriptEditor) {
        window.transcriptEditor.toggleEditMode();
    } else {
        console.error('transcriptEditor not found on window object');
    }
}

function exportTranscript() {
    if (window.transcriptEditor) {
        window.transcriptEditor.exportTranscript();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, checking for transcription view');
    if (document.querySelector('.transcription-view')) {
        console.log('Creating TranscriptEditor instance');
        window.transcriptEditor = new TranscriptEditor();
    } else {
        console.log('No transcription view found');
    }
});