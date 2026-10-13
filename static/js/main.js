/**
 * Student Portal — Main JavaScript
 * Particle dot field animation, sidebar, utilities, toast system
 */

(function () {
    'use strict';

    /* ========================================
       Sidebar Toggle Logic
       Handles decoupled behavior for mobile (open) vs desktop (collapsed)
       ======================================== */
    window.toggleSidebar = function () {
        const sidebar = document.getElementById('sidebar');
        if (!sidebar) return;

        const isMobile = window.innerWidth < 900;

        if (isMobile) {
            sidebar.classList.toggle('open');
        } else {
            sidebar.classList.toggle('collapsed');
        }
    };

    window.toggleTheme = function () {
        const html = document.documentElement;
        const currentTheme = html.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        html.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);

        const icon = document.getElementById('theme-icon');
        if (icon) {
            icon.innerHTML = newTheme === 'dark'
                ? '<path d="M21 12.79A9 9 0 1 1 11.21 3 9 9 0 0 1 21 12.79z"></path>' // Moon
                : '<circle cx="12" cy="12" r="5"/><line x1="12" x2="12" y1="1" y2="3"/><line x1="12" x2="12" y1="21" y2="23"/><line x1="4.22" x2="4.22" y1="4.22" y2="4.22"/><line x1="18.78" x2="18.78" y1="18.78" y2="18.78"/><line x1="4.22" x2="4.22" y1="18.78" y2="18.78"/><line x1="18.78" x2="18.78" y1="4.22" y2="4.22"/>'; // Sun
        }
    };

    /* ========================================
       Particle Dot Field
       Slowly drifting dots with subtle connections
       ======================================== */
    const canvas = document.getElementById('particle-canvas');
    if (canvas) {
        const ctx = canvas.getContext('2d');
        let particles = [];
        let mouseX = -1000;
        let mouseY = -1000;
        let animationId = null;
        let isVisible = true;

        const PARTICLE_COUNT = 70;
        const CONNECTION_DISTANCE = 120;
        const MOUSE_RADIUS = 150;

        function resize() {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        }

        class Particle {
            constructor() {
                this.reset(true);
            }

            reset(initial) {
                this.x = Math.random() * canvas.width;
                this.y = Math.random() * canvas.height;
                this.size = Math.random() * 2 + 0.5;
                this.speedX = (Math.random() - 0.5) * 0.35;
                this.speedY = (Math.random() - 0.5) * 0.35;
                this.opacity = Math.random() * 0.5 + 0.15;
                if (!initial) {
                    this.x = Math.random() * canvas.width;
                    this.y = Math.random() * canvas.height;
                }
            }

            update() {
                this.x += this.speedX;
                this.y += this.speedY;

                // Wrap around edges gently
                if (this.x < -10) this.x = canvas.width + 10;
                if (this.x > canvas.width + 10) this.x = -10;
                if (this.y < -10) this.y = canvas.height + 10;
                if (this.y > canvas.height + 10) this.y = -10;

                // Gentle mouse repulsion
                const dx = this.x - mouseX;
                const dy = this.y - mouseY;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < MOUSE_RADIUS && dist > 0) {
                    const force = (MOUSE_RADIUS - dist) / MOUSE_RADIUS * 0.5;
                    this.x += (dx / dist) * force;
                    this.y += (dy / dist) * force;
                }
            }

            draw() {
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(59, 77, 138, ${this.opacity})`;
                ctx.fill();
            }
        }

        function initParticles() {
            particles = [];
            for (let i = 0; i < PARTICLE_COUNT; i++) {
                particles.push(new Particle());
            }
        }

        function drawConnections() {
            for (let i = 0; i < particles.length; i++) {
                for (let j = i + 1; j < particles.length; j++) {
                    const dx = particles[i].x - particles[j].x;
                    const dy = particles[i].y - particles[j].y;
                    const dist = Math.sqrt(dx * dx + dy * dy);

                    if (dist < CONNECTION_DISTANCE) {
                        const opacity = (1 - dist / CONNECTION_DISTANCE) * 0.12;
                        ctx.beginPath();
                        ctx.moveTo(particles[i].x, particles[i].y);
                        ctx.lineTo(particles[j].x, particles[j].y);
                        ctx.strokeStyle = `rgba(91, 115, 181, ${opacity})`;
                        ctx.lineWidth = 0.5;
                        ctx.stroke();
                    }
                }
            }
        }

        function animate() {
            if (!isVisible) {
                // When tab hidden, just resample positions occasionally
                if (Math.random() < 0.01) {
                    particles.forEach(p => {
                        p.x += (Math.random() - 0.5) * 2;
                        p.y += (Math.random() - 0.5) * 2;
                    });
                }
                animationId = requestAnimationFrame(animate);
                return;
            }

            ctx.clearRect(0, 0, canvas.width, canvas.height);
            particles.forEach(p => {
                p.update();
                p.draw();
            });
            drawConnections();
            animationId = requestAnimationFrame(animate);
        }

        function handleVisibility() {
            isVisible = !document.hidden;
        }

        function handleMouseMove(e) {
            mouseX = e.clientX;
            mouseY = e.clientY;
        }

        function handleTouchMove(e) {
            if (e.touches.length > 0) {
                mouseX = e.touches[0].clientX;
                mouseY = e.touches[0].clientY;
            }
        }

        window.addEventListener('resize', resize);
        document.addEventListener('visibilitychange', handleVisibility);
        document.addEventListener('mousemove', handleMouseMove, { passive: true });
        document.addEventListener('touchmove', handleTouchMove, { passive: true });

        resize();
        initParticles();
        animate();

        // Cleanup on page unload
        window.addEventListener('beforeunload', function () {
            if (animationId) cancelAnimationFrame(animationId);
            window.removeEventListener('resize', resize);
            document.removeEventListener('visibilitychange', handleVisibility);
            document.removeEventListener('mousemove', handleMouseMove);
        });
    }

    /* ========================================
       Toast Notification System
       ======================================== */
    window.showToast = function (message, type) {
        type = type || 'info';
        var container = document.getElementById('toast-container');
        if (!container) return;

        var icons = {
            success: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
            error: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" x2="9" y1="9" y2="15"/><line x1="9" x2="15" y1="9" y2="15"/></svg>',
            info: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="16" y2="12"/><line x1="12" x2="12.01" y1="8" y2="8"/></svg>'
        };

        var toast = document.createElement('div');
        toast.className = 'toast ' + type;
        toast.innerHTML =
            '<span class="toast-icon">' + (icons[type] || icons.info) + '</span>' +
            '<span>' + message + '</span>' +
            '<button class="toast-close" onclick="this.parentElement.remove()">' +
                '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" x2="6" y1="6" y2="18"/><line x1="6" x2="18" y1="6" y2="18"/></svg>' +
            '</button>';

        container.appendChild(toast);

        setTimeout(function () {
            if (toast.parentElement) {
                toast.style.transition = 'opacity 0.2s ease, transform 0.2s ease';
                toast.style.opacity = '0';
                toast.style.transform = 'translateX(40px)';
                setTimeout(function () {
                    if (toast.parentElement) toast.remove();
                }, 200);
            }
        }, 3500);
    };

    /* ========================================
       Utility functions
       ======================================== */
    window.formatDate = function (dateStr) {
        if (!dateStr) return '—';
        var parts = dateStr.split('T')[0].split('-');
        if (parts.length !== 3) return dateStr;
        var d = new Date(parts[0], parts[1] - 1, parts[2]);
        return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
    };

    window.formatTime = function (dateStr) {
        if (!dateStr) return '—';
        var parts = dateStr.split('T');
        if (parts.length === 2) {
            var timePart = parts[1].split('.')[0];
            if (timePart) return timePart.substring(0, 5);
        }
        return '';
    };

    window.getGradeColor = function (grade) {
        if (!grade || grade === 'IP') return 'var(--text-muted)';
        var g = grade.charAt(0);
        if (g === 'A') return 'var(--success)';
        if (g === 'B') return 'var(--indigo-600)';
        if (g === 'C') return 'var(--warning)';
        if (g === 'D') return 'var(--warning)';
        if (g === 'F') return 'var(--error)';
        return 'var(--text-muted)';
    };

    /* ========================================
       Page load entrance animations
       Already handled by CSS, but we re-trigger
       for dynamically loaded content
       ======================================== */
    window.observeEntranceAnimations = function () {
        if (!('IntersectionObserver' in window)) return;
        var animated = new Set();
        var observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting && !animated.has(entry.target)) {
                    animated.add(entry.target);
                    entry.target.style.animationPlayState = 'running';
                }
            });
        }, { threshold: 0.1 });

        document.querySelectorAll('.stat-card, .course-card, .content-card, .form-card, .profile-card, .quick-action, .announcement-item, .enrollment-student-row, .material-item, .student-list-item').forEach(function (el) {
            // These already have animation-play-state: running from CSS
            // We use this for any dynamic content added later
        });

        observer.disconnect();
    };

    document.addEventListener('DOMContentLoaded', function () {
        // Load saved theme
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);

        // Update theme icon
        const icon = document.getElementById('theme-icon');
        if (icon) {
            icon.innerHTML = savedTheme === 'dark'
                ? '<path d="M21 12.79A9 9 0 1 1 11.21 3 9 9 0 0 1 21 12.79z"></path>'
                : '<circle cx="12" cy="12" r="5"/><line x1="12" x2="12" y1="1" y2="3"/><line x1="12" x2="12" y1="21" y2="23"/><line x1="4.22" x2="4.22" y1="4.22" y2="4.22"/><line x1="18.78" x2="18.78" y1="18.78" y2="18.78"/><line x1="4.22" x2="4.22" y1="18.78" y2="18.78"/><line x1="18.78" x2="18.78" y1="4.22" y2="4.22"/>';
        }

        observeEntranceAnimations();
    });

})();
