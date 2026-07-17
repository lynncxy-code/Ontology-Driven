/**
 * Lingjing Core - Presentation Template JavaScript
 * 灵境核心 - 演示文稿模板 JavaScript
 *
 * @version 2.7.1
 * @description 演示文稿场景专用 - 交互脚本
 * @design 基于参考文件"1月工作汇报演示/presentation.html"的功能
 */

class PresentationController {
  constructor() {
    this.slides = [];
    this.currentIndex = 0;
    this.totalSlides = 0;
    this.htmlElement = document.documentElement;
    this.theme = 'light';
    this.init();
  }

  init() {
    this.slides = document.querySelectorAll('.presentation-slide');
    this.totalSlides = this.slides.length;

    if (this.totalSlides === 0) {
      console.warn('未找到演示文稿幻灯片');
      return;
    }

    // 恢复上次查看的幻灯片
    this.restoreProgress();

    this.updateSlides();
    this.bindEvents();
    this.updateProgress();
    this.createIndicators();
    this.createNavigation();
    this.createThemeToggle();
    this.createProgressBar();
    this.createFloatingShapes();
    this.createParticles();
    this.createModal();
  }

  updateSlides() {
    this.slides.forEach((slide, index) => {
      slide.classList.toggle('active', index === this.currentIndex);
    });

    this.updateIndicators();
    this.updateNavButtons();
    this.updateProgress();
  }

  bindEvents() {
    document.addEventListener('keydown', (e) => this.handleKeydown(e));

    let touchStartX = 0;
    let touchEndX = 0;

    document.addEventListener('touchstart', (e) => {
      touchStartX = e.changedTouches[0].screenX;
    });

    document.addEventListener('touchend', (e) => {
      touchEndX = e.changedTouches[0].screenX;
      this.handleSwipe(touchStartX, touchEndX);
    });
  }

  handleKeydown(e) {
    switch(e.key) {
      case 'ArrowRight':
      case ' ':
      case 'Enter':
        e.preventDefault();
        this.nextSlide();
        break;
      case 'ArrowLeft':
        e.preventDefault();
        this.prevSlide();
        break;
      case 'Escape':
        this.closeModal();
        break;
    }
  }

  handleSwipe(startX, endX) {
    const threshold = 50;
    const diff = startX - endX;

    if (Math.abs(diff) > threshold) {
      if (diff > 0) {
        this.nextSlide();
      } else {
        this.prevSlide();
      }
    }
  }

  nextSlide() {
    if (this.currentIndex < this.totalSlides - 1) {
      this.currentIndex++;
      this.updateSlides();
      this.saveProgress();
    }
  }

  prevSlide() {
    if (this.currentIndex > 0) {
      this.currentIndex--;
      this.updateSlides();
      this.saveProgress();
    }
  }

  goToSlide(index) {
    if (index >= 0 && index < this.totalSlides) {
      this.currentIndex = index;
      this.updateSlides();
      this.saveProgress();
    }
  }

  saveProgress() {
    try {
      sessionStorage.setItem('presentationSlideIndex', this.currentIndex);
    } catch (e) {
      console.warn('无法保存演示文稿进度');
    }
  }

  restoreProgress() {
    try {
      const savedIndex = sessionStorage.getItem('presentationSlideIndex');
      if (savedIndex !== null) {
        const index = parseInt(savedIndex, 10);
        if (index >= 0 && index < this.totalSlides) {
          this.currentIndex = index;
        }
      }
    } catch (e) {
      console.warn('无法恢复演示文稿进度');
    }
  }

  createIndicators() {
    let indicatorsContainer = document.querySelector('.presentation-slide-indicators');

    if (!indicatorsContainer) {
      indicatorsContainer = document.createElement('div');
      indicatorsContainer.className = 'presentation-slide-indicators';
      document.body.appendChild(indicatorsContainer);
    }

    indicatorsContainer.innerHTML = '';

    for (let i = 0; i < this.totalSlides; i++) {
      const indicator = document.createElement('button');
      indicator.className = 'presentation-slide-indicator' + (i === this.currentIndex ? ' active' : '');
      indicator.setAttribute('aria-label', `跳转到第 ${i + 1} 页`);
      indicator.addEventListener('click', () => this.goToSlide(i));
      indicatorsContainer.appendChild(indicator);
    }
  }

  updateIndicators() {
    const indicators = document.querySelectorAll('.presentation-slide-indicator');
    indicators.forEach((indicator, index) => {
      indicator.classList.toggle('active', index === this.currentIndex);
    });
  }

  createNavigation() {
    let navContainer = document.querySelector('.presentation-nav-buttons');

    if (!navContainer) {
      navContainer = document.createElement('div');
      navContainer.className = 'presentation-nav-buttons';
      document.body.appendChild(navContainer);
    }

    navContainer.innerHTML = `
      <button class="presentation-nav-btn presentation-prev-btn" id="presentation-prev-btn" aria-label="上一页">
        <i data-lucide="chevron-left"></i>
      </button>
      <button class="presentation-nav-btn presentation-next-btn" id="presentation-next-btn" aria-label="下一页">
        <i data-lucide="chevron-right"></i>
      </button>
    `;

    if (typeof lucide !== 'undefined') {
      lucide.createIcons();
    }

    const prevBtn = document.getElementById('presentation-prev-btn');
    const nextBtn = document.getElementById('presentation-next-btn');

    if (prevBtn) {
      prevBtn.addEventListener('click', () => this.prevSlide());
    }
    if (nextBtn) {
      nextBtn.addEventListener('click', () => this.nextSlide());
    }

    this.updateNavButtons();
  }

  updateNavButtons() {
    const prevBtn = document.getElementById('presentation-prev-btn');
    const nextBtn = document.getElementById('presentation-next-btn');

    if (prevBtn) {
      prevBtn.disabled = this.currentIndex === 0;
    }

    if (nextBtn) {
      nextBtn.disabled = this.currentIndex === this.totalSlides - 1;
    }
  }

  createThemeToggle() {
    let toggleContainer = document.querySelector('.presentation-theme-toggle');

    if (!toggleContainer) {
      toggleContainer = document.createElement('div');
      toggleContainer.className = 'presentation-theme-toggle';
      document.body.appendChild(toggleContainer);
    }

    toggleContainer.innerHTML = `
      <button class="presentation-theme-btn" id="presentation-theme-btn" aria-label="切换主题">
        <span id="presentation-theme-icon">🌙</span>
      </button>
    `;

    const themeBtn = document.getElementById('presentation-theme-btn');
    if (themeBtn) {
      themeBtn.addEventListener('click', () => this.toggleTheme());
    }

    let savedTheme = 'light';
    try {
      savedTheme = localStorage.getItem('lingjing-presentation-theme') || 'light';
    } catch (e) {
      console.warn('无法读取主题设置');
    }
    if (savedTheme) {
      this.theme = savedTheme;
      this.htmlElement.setAttribute('data-theme', this.theme);
      this.updateThemeIcon();
    }
  }

  toggleTheme() {
    this.theme = this.theme === 'light' ? 'dark' : 'light';
    this.htmlElement.setAttribute('data-theme', this.theme);
    try {
      localStorage.setItem('lingjing-presentation-theme', this.theme);
    } catch (e) {
      console.warn('无法保存主题设置');
    }
    this.updateThemeIcon();
  }

  updateThemeIcon() {
    const icon = document.getElementById('presentation-theme-icon');
    if (icon) {
      icon.textContent = this.theme === 'light' ? '🌙' : '☀️';
    }
  }

  createProgressBar() {
    let progressBar = document.querySelector('.presentation-progress-bar');

    if (!progressBar) {
      progressBar = document.createElement('div');
      progressBar.className = 'presentation-progress-bar';
      progressBar.id = 'presentation-progress-bar';
      document.body.appendChild(progressBar);
    }
  }

  updateProgress() {
    const progressBar = document.getElementById('presentation-progress-bar');
    if (progressBar) {
      const progress = ((this.currentIndex + 1) / this.totalSlides) * 100;
      progressBar.style.width = progress + '%';
    }
  }

  createFloatingShapes() {
    let shapesContainer = document.querySelector('.presentation-floating-shapes');

    if (!shapesContainer) {
      shapesContainer = document.createElement('div');
      shapesContainer.className = 'presentation-floating-shapes';
      shapesContainer.innerHTML = `
        <div class="presentation-shape presentation-shape-1"></div>
        <div class="presentation-shape presentation-shape-2"></div>
        <div class="presentation-shape presentation-shape-3"></div>
      `;
      const firstChild = document.body.firstChild;
      if (firstChild) {
        document.body.insertBefore(shapesContainer, firstChild);
      } else {
        document.body.appendChild(shapesContainer);
      }
    }
  }

  createParticles() {
    const container = document.querySelector('.presentation-particles');
    if (!container) return;

    // 限制粒子数量以提升性能
    const particleCount = Math.min(window.innerWidth < 768 ? 10 : 30, 30);

    for (let i = 0; i < particleCount; i++) {
      const particle = document.createElement('div');
      particle.className = 'presentation-particle';
      particle.style.left = Math.random() * 100 + '%';
      particle.style.top = 100 + Math.random() * 100 + '%';
      particle.style.animationDelay = Math.random() * 20 + 's';
      particle.style.animationDuration = (15 + Math.random() * 15) + 's';
      container.appendChild(particle);
    }
  }

  createModal() {
    let modal = document.querySelector('.presentation-modal');

    if (!modal) {
      modal = document.createElement('div');
      modal.className = 'presentation-modal';
      modal.id = 'presentation-modal';
      modal.innerHTML = `
        <div class="presentation-modal-content">
          <button class="presentation-modal-close" id="presentation-modal-close" aria-label="关闭">×</button>
          <div id="presentation-modal-body"></div>
        </div>
      `;
      document.body.appendChild(modal);

      const closeBtn = document.getElementById('presentation-modal-close');
      if (closeBtn) {
        closeBtn.addEventListener('click', () => this.closeModal());
      }

      modal.addEventListener('click', (e) => {
        if (e.target === modal) {
          this.closeModal();
        }
      });
    }
  }

  openModal(coverSrc, videoSrc = null) {
    const modal = document.getElementById('presentation-modal');
    const modalBody = document.getElementById('presentation-modal-body');

    if (!modal || !modalBody) return;

    if (videoSrc) {
      modalBody.innerHTML = `<video src="${videoSrc}" controls autoplay muted style="max-width: 100%; max-height: 90vh; border-radius: 20px; box-shadow: var(--presentation-glow-primary);"></video>`;
    } else if (coverSrc.endsWith('.mp4') || coverSrc.endsWith('.webm')) {
      modalBody.innerHTML = `<video src="${coverSrc}" controls autoplay muted style="max-width: 100%; max-height: 90vh; border-radius: 20px; box-shadow: var(--presentation-glow-primary);"></video>`;
    } else {
      modalBody.innerHTML = `<img src="${coverSrc}" alt="预览" style="max-width: 100%; max-height: 90vh; border-radius: 20px; box-shadow: var(--presentation-glow-primary);">`;
    }

    modal.classList.add('active');
  }

  closeModal() {
    const modal = document.getElementById('presentation-modal');
    const modalBody = document.getElementById('presentation-modal-body');

    if (modal) {
      modal.classList.remove('active');
    }

    if (modalBody) {
      modalBody.innerHTML = '';
    }
  }

  getCurrentSlide() {
    return this.slides[this.currentIndex];
  }

  getCurrentIndex() {
    return this.currentIndex;
  }

  getTotalSlides() {
    return this.totalSlides;
  }

  getTheme() {
    return this.theme;
  }
}

(function() {
  document.addEventListener('DOMContentLoaded', function() {
    if (!window.presentationController) {
      window.presentationController = new PresentationController();
    }
  });
})();
