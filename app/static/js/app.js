/**
 * xiaokeda App JavaScript
 */

(function() {
    'use strict';

    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Form validation
    var forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Confirm delete actions
    document.querySelectorAll('[data-confirm]').forEach(function(el) {
        el.addEventListener('click', function(e) {
            var message = el.getAttribute('data-confirm') || '确定要执行此操作吗？';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // Mobile sidebar toggle
    var sidebar = document.querySelector('.sidebar');
    if (sidebar) {
        var toggler = document.querySelector('.navbar-toggler');
        if (toggler) {
            toggler.addEventListener('click', function() {
                sidebar.classList.toggle('show');
            });
        }
    }

    // Date picker initialization (if available)
    if (typeof bootstrap !== 'undefined' && bootstrap.Datepicker) {
        document.querySelectorAll('input[type="date"]').forEach(function(input) {
            input.classList.add('form-control');
        });
    }

    // File upload preview
    document.querySelectorAll('input[type="file"]').forEach(function(input) {
        input.addEventListener('change', function(e) {
            var fileName = e.target.files[0]?.name;
            var label = input.nextElementSibling;
            if (label && label.classList.contains('custom-file-label')) {
                label.textContent = fileName || '选择文件';
            }
        });
    });

    // AJAX CSRF token handling
    var csrfToken = document.querySelector('meta[name="csrf-token"]');
    if (csrfToken) {
        var token = csrfToken.getAttribute('content');
        document.addEventListener('fetch', function(e) {
            if (e.request.url.startsWith(window.location.origin)) {
                e.request.headers.set('X-CSRFToken', token);
            }
        });
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + Enter to submit forms
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            var form = document.querySelector('form:has([type="submit"]:focus)');
            if (form) {
                form.submit();
            }
        }
    });

})();
