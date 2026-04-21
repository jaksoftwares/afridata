/**
 * AFRIDATA - Main JavaScript
 * Interactive functionality for data standardisation workflow
 */

(function() {
    'use strict';

    // =========================================================================
    // DRAG & DROP FILE UPLOAD
    // =========================================================================
    
    function initDragDrop() {
        const dragDropArea = document.getElementById('dragDropArea');
        const fileInput = document.getElementById('fileInput');

        if (!dragDropArea) return;

        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dragDropArea.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        // Highlight drop area when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            dragDropArea.addEventListener(eventName, () => {
                dragDropArea.classList.add('drag-over');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dragDropArea.addEventListener(eventName, () => {
                dragDropArea.classList.remove('drag-over');
            }, false);
        });

        // Handle dropped files
        dragDropArea.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            fileInput.files = files;
            handleFileSelect(files[0]);
        }, false);

        // Handle file input change
        fileInput.addEventListener('change', (e) => {
            handleFileSelect(e.target.files[0]);
        });

        // Click to browse
        dragDropArea.addEventListener('click', () => fileInput.click());
    }

    function handleFileSelect(file) {
        if (!file) return;

        const fileInfo = document.getElementById('fileInfo');
        if (fileInfo) {
            const sizeInMB = (file.size / (1024 * 1024)).toFixed(2);
            fileInfo.innerHTML = `
                <div class="alert alert-info">
                    <strong>File selected:</strong> ${file.name} (${sizeInMB} MB)
                </div>
            `;
        }

        // Preview file if preview endpoint exists
        previewFile(file);
    }

    function previewFile(file) {
        const previewContainer = document.getElementById('filePreview');
        if (!previewContainer) return;

        const formData = new FormData();
        formData.append('file', file);
        formData.append('preview_rows', 5);

        // Show loading
        previewContainer.innerHTML = '<div class="spinner"></div> Loading preview...';

        fetch('/standardiser/api/preview/', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayPreview(data);
            } else {
                previewContainer.innerHTML = `<div class="alert alert-danger">Preview failed: ${data.error}</div>`;
            }
        })
        .catch(error => {
            console.error('Preview error:', error);
            previewContainer.innerHTML = '<div class="alert alert-danger">Failed to preview file</div>';
        });
    }

    function displayPreview(data) {
        const previewContainer = document.getElementById('filePreview');
        if (!data.columns || !data.rows) return;

        let html = `
            <div class="card">
                <div class="card-header">
                    <h6 class="mb-0">File Preview (${data.row_count} rows)</h6>
                </div>
                <div class="table-responsive">
                    <table class="table table-sm mb-0">
                        <thead>
                            <tr>
        `;

        // Add column headers
        data.columns.forEach(col => {
            html += `<th>${escapeHtml(col)}</th>`;
        });

        html += `
                            </tr>
                        </thead>
                        <tbody>
        `;

        // Add data rows
        if (Array.isArray(data.rows)) {
            data.rows.forEach(row => {
                html += '<tr>';
                data.columns.forEach(col => {
                    const value = row[col] || '';
                    html += `<td>${escapeHtml(String(value).substring(0, 50))}</td>`;
                });
                html += '</tr>';
            });
        }

        html += `
                        </tbody>
                    </table>
                </div>
            </div>
        `;

        previewContainer.innerHTML = html;
    }

    // =========================================================================
    // FORM VALIDATION
    // =========================================================================

    function initFormValidation() {
        const forms = document.querySelectorAll('[data-validate="true"]');
        forms.forEach(form => {
            form.addEventListener('submit', function(e) {
                if (!validateForm(this)) {
                    e.preventDefault();
                }
            });
        });
    }

    function validateForm(form) {
        let isValid = true;
        const requiredFields = form.querySelectorAll('[required]');

        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                markFieldInvalid(field);
                isValid = false;
            } else {
                markFieldValid(field);
            }
        });

        return isValid;
    }

    function markFieldInvalid(field) {
        field.classList.remove('is-valid');
        field.classList.add('is-invalid');
    }

    function markFieldValid(field) {
        field.classList.remove('is-invalid');
        field.classList.add('is-valid');
    }

    // =========================================================================
    // QUALITY SCORE VISUALIZATION
    // =========================================================================

    function initScoreVisualizations() {
        const scoreElements = document.querySelectorAll('[data-score]');
        scoreElements.forEach(element => {
            const score = parseFloat(element.dataset.score);
            const color = getScoreColor(score);
            element.style.color = color;

            // Create visual bar if container exists
            const barContainer = element.closest('.score-container');
            if (barContainer) {
                const bar = barContainer.querySelector('.score-bar');
                if (bar) {
                    bar.style.width = score + '%';
                    bar.style.backgroundColor = color;
                }
            }
        });
    }

    function getScoreColor(score) {
        if (score >= 80) return '#27ae60'; // Green
        if (score >= 60) return '#f39c12'; // Orange
        return '#e74c3c'; // Red
    }

    // =========================================================================
    // DATA TABLE INTERACTIONS
    // =========================================================================

    function initTableInteractions() {
        // Row hover effect
        const tables = document.querySelectorAll('.table');
        tables.forEach(table => {
            const rows = table.querySelectorAll('tbody tr');
            rows.forEach(row => {
                row.addEventListener('mouseenter', () => {
                    row.style.backgroundColor = '#f5f5f5';
                });
                row.addEventListener('mouseleave', () => {
                    row.style.backgroundColor = '';
                });
            });
        });

        // Sortable tables
        initSortableTables();
    }

    function initSortableTables() {
        const tables = document.querySelectorAll('table[data-sortable="true"]');
        tables.forEach(table => {
            const headers = table.querySelectorAll('th');
            headers.forEach((header, index) => {
                header.style.cursor = 'pointer';
                header.addEventListener('click', () => {
                    sortTable(table, index);
                });
            });
        });
    }

    function sortTable(table, columnIndex) {
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const isAscending = table.dataset.sortAsc === 'true';

        rows.sort((a, b) => {
            const aValue = a.children[columnIndex].textContent.trim();
            const bValue = b.children[columnIndex].textContent.trim();

            if (!isNaN(aValue) && !isNaN(bValue)) {
                return isAscending ? aValue - bValue : bValue - aValue;
            }
            return isAscending ? aValue.localeCompare(bValue) : bValue.localeCompare(aValue);
        });

        rows.forEach(row => tbody.appendChild(row));
        table.dataset.sortAsc = !isAscending;
    }

    // =========================================================================
    // TOAST NOTIFICATIONS
    // =========================================================================

    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} position-fixed`;
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        toast.textContent = message;

        document.body.appendChild(toast);

        // Hide after 5 seconds
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transition = 'opacity 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    }

    // =========================================================================
    // CONFIRMATION DIALOGS
    // =========================================================================

    function initConfirmationDialogs() {
        document.addEventListener('click', function(e) {
            if (e.target.matches('[data-confirm]')) {
                const message = e.target.dataset.confirm;
                if (!confirm(message)) {
                    e.preventDefault();
                }
            }
        });
    }

    // =========================================================================
    // UTILITY FUNCTIONS
    // =========================================================================

    function escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }

    // =========================================================================
    // INITIALIZATION
    // =========================================================================

    document.addEventListener('DOMContentLoaded', function() {
        initDragDrop();
        initFormValidation();
        initScoreVisualizations();
        initTableInteractions();
        initConfirmationDialogs();

        console.log('[AFRIDATA] All scripts initialized');
    });

    // Expose utility functions globally if needed
    window.AFRIDATA = {
        showToast,
        escapeHtml
    };

})();
