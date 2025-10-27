// Log Management JavaScript - Cards for log levels with save buttons
class LogManager {
    constructor() {
        this.currentLogFile = null;
        this.initializeEventListeners();
        this.loadLogLevels();
    }

    initializeEventListeners() {
        // Lines select change
        DOMUtils.addSafeEventListener('linesSelect', 'change', () => {
            if (this.currentLogFile) {
                this.loadLogFile(this.currentLogFile);
            }
        });
    }

    getLevelBadgeClass(level) {
        const classes = {
            'DEBUG': 'info',
            'INFO': 'success',
            'WARNING': 'warning',
            'ERROR': 'danger',
            'CRITICAL': 'dark'
        };
        return classes[level] || 'secondary';
    }

    async loadLogLevels() {
        try {
            const data = await ApiClient.get('/admin/api/logs/levels');

            if (data.success) {
                this.renderLogLevelsCards(data.data.levels);
            } else {
                NotificationManager.show('Error loading log levels: ' + data.message, 'error');
            }
        } catch (error) {
            console.error('Error loading log levels:', error);
            NotificationManager.show('Error loading log levels', 'error');
        }
    }

    renderLogLevelsCards(levels) {
        const container = document.getElementById('logLevelsCards');
        if (!container) return;

        container.innerHTML = '';

        for (const [service, info] of Object.entries(levels)) {
            const level = info.level || 'INFO';
            const description = info.description || `Log level for ${service} service`;

            const card = document.createElement('div');
            card.className = 'col-md-6 col-lg-4 mb-4';
            card.innerHTML = `
                <div class="card log-level-card h-100">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h6 class="mb-0 text-capitalize">${this.escapeHtml(service)}</h6>
                        <span class="badge bg-${this.getLevelBadgeClass(level)}">${this.escapeHtml(level)}</span>
                    </div>
                    <div class="card-body">
                        <p class="card-text small text-muted mb-3">${this.escapeHtml(description)}</p>
                        <div class="form-group mb-3">
                            <label class="form-label small fw-bold">Change Level:</label>
                            <select class="form-select form-select-sm" id="level-select-${this.escapeHtml(service)}">
                                <option value="DEBUG" ${level === 'DEBUG' ? 'selected' : ''}>DEBUG</option>
                                <option value="INFO" ${level === 'INFO' ? 'selected' : ''}>INFO</option>
                                <option value="WARNING" ${level === 'WARNING' ? 'selected' : ''}>WARNING</option>
                                <option value="ERROR" ${level === 'ERROR' ? 'selected' : ''}>ERROR</option>
                                <option value="CRITICAL" ${level === 'CRITICAL' ? 'selected' : ''}>CRITICAL</option>
                            </select>
                        </div>
                    </div>
                    <div class="card-footer bg-transparent">
                        <button type="button" class="btn btn-primary btn-sm w-100"
                                onclick="logManager.saveLogLevel('${this.escapeHtml(service)}')">
                            <i class="bi bi-check-lg me-1"></i> Save Level
                        </button>
                    </div>
                </div>
            `;
            container.appendChild(card);
        }
    }

    async saveLogLevel(service) {
        const select = document.getElementById(`level-select-${service}`);
        if (!select) return;

        const level = select.value;
        const originalValue = select.getAttribute('data-original-value') || level;

        // Show loading state
        const saveButton = select.closest('.card').querySelector('button');
        const originalText = saveButton.innerHTML;
        saveButton.innerHTML = '<i class="bi bi-arrow-repeat spinner"></i> Saving...';
        saveButton.disabled = true;

        try {
            const data = await ApiClient.post('/admin/api/logs/level', {
                service_name: service,
                level: level
            });

            if (data.success) {
                NotificationManager.show(data.message, 'success');
                // Update the badge
                const badge = select.closest('.card').querySelector('.badge');
                if (badge) {
                    badge.textContent = level;
                    badge.className = `badge bg-${this.getLevelBadgeClass(level)}`;
                }
                // Store the new value as original
                select.setAttribute('data-original-value', level);
            } else {
                NotificationManager.show(data.message, 'error');
                // Revert to original value
                select.value = originalValue;
            }
        } catch (error) {
            console.error('Error updating log level:', error);
            NotificationManager.show('Error updating log level', 'error');
            // Revert to original value
            select.value = originalValue;
        } finally {
            // Restore button state
            saveButton.innerHTML = originalText;
            saveButton.disabled = false;
        }
    }

    async viewLogFile(filename) {
        const lines = document.getElementById('linesSelect')?.value || 100;
        await this.loadLogFile(filename, lines);
    }

    async loadLogFile(filename, lines = 100) {
        if (!filename) {
            NotificationManager.show('Please select a log file', 'warning');
            return;
        }

        this.currentLogFile = filename;

        // Show loading state
        const logContent = document.getElementById('logContent');
        if (logContent) {
            logContent.textContent = 'Loading...';
        }

        const logContentCard = document.getElementById('logContentCard');
        if (logContentCard) {
            logContentCard.style.display = 'block';
        }

        try {
            const data = await ApiClient.get(`/admin/api/logs/${filename}?lines=${lines}`);

            if (data.success) {
                this.displayLogContent(filename, lines, data.data.content);
                // Scroll to show the log content
                document.getElementById('logContentCard').scrollIntoView({ behavior: 'smooth' });
            } else {
                NotificationManager.show(data.message, 'error');
                this.closeLogView();
            }
        } catch (error) {
            console.error('Error loading log file:', error);
            NotificationManager.show('Error loading log file', 'error');
            this.closeLogView();
        }
    }

    displayLogContent(filename, lines, content) {
        const logContent = document.getElementById('logContent');
        const logContentCard = document.getElementById('logContentCard');
        const logContentTitle = document.getElementById('logContentTitle');

        if (!logContent || !logContentCard || !logContentTitle) return;

        logContentTitle.textContent = `Log Content: ${filename} (Last ${lines} lines)`;
        logContent.textContent = Array.isArray(content) ? content.join('') : content;
        logContentCard.style.display = 'block';

        // Scroll to bottom
        setTimeout(() => {
            logContent.scrollTop = logContent.scrollHeight;
        }, 100);
    }

    closeLogView() {
        const logContentCard = document.getElementById('logContentCard');
        if (logContentCard) {
            logContentCard.style.display = 'none';
            this.currentLogFile = null;
        }
    }

    async clearLogFile(filename) {
        if (!filename) {
            NotificationManager.show('Please select a log file', 'warning');
            return;
        }

        if (!confirm(`Are you sure you want to clear ${filename}? This action cannot be undone.`)) {
            return;
        }

        try {
            const data = await ApiClient.post(`/admin/api/logs/${filename}/clear`);

            if (data.success) {
                NotificationManager.show(data.message, 'success');
                this.closeLogView();
                // Refresh page to update file sizes
                setTimeout(() => location.reload(), 1000);
            } else {
                NotificationManager.show(data.message, 'error');
            }
        } catch (error) {
            console.error('Error clearing log file:', error);
            NotificationManager.show('Error clearing log file', 'error');
        }
    }

    copyLogContent() {
        const logContent = document.getElementById('logContent');
        if (!logContent) return;

        const textArea = document.createElement('textarea');
        textArea.value = logContent.textContent;
        document.body.appendChild(textArea);
        textArea.select();

        try {
            const successful = document.execCommand('copy');
            if (successful) {
                NotificationManager.show('Log content copied to clipboard', 'success');
            } else {
                NotificationManager.show('Failed to copy log content', 'warning');
            }
        } catch (err) {
            console.error('Error copying text: ', err);
            NotificationManager.show('Error copying log content', 'error');
        }

        document.body.removeChild(textArea);
    }

    refreshLogs() {
        location.reload();
    }

    escapeHtml(unsafe) {
        if (typeof unsafe !== 'string') return unsafe;
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
}

// Initialize Log Manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.logManager = new LogManager();
});