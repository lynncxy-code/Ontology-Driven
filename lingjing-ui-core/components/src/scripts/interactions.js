/**
 * Lingjing Core - 交互效果脚本
 *
 * @version 2.7.1
 * @description 为 Lingjing Core 组件提供默认的交互效果
 * @update 2026-02-25 - 修复性能和兼容性问题
 * @author Lingjing Core Team
 * @license MIT
 *
 * 功能包括：
 * - 卡片涟漪效果：鼠标进入时的蓝色波纹扩散动画
 * - 滚动动画：卡片进入视口时的渐显动画
 * - 主题管理：深浅色主题自动切换和持久化
 *
 * 使用方法：
 * 1. 在 HTML 底部引入此脚本：
 *    <script src="lingjing-core/components/src/scripts/interactions.js"></script>
 *
 * 2. 使用标准卡片类即可自动生效：
 *    <div class="card-glass">卡片内容</div>
 *
 * 3. 支持的卡片类：
 *    - .card-glass
 *    - .glass-card
 *    - .glass-flowing
 *    - .glass-frosted
 *    - .glass-colored
 *
 * 4. 全局 API（可选）：
 *    - window.Lingjing.toggleTheme()  // 切换主题
 *    - window.Lingjing.setTheme('dark')  // 设置主题
 *    - window.Lingjing.getTheme()  // 获取当前主题
 *
 * 详细文档：https://lingjing-core.com/docs/INTERACTIONS.md
 */

// ============================================================================
// 卡片涟漪效果 - Card Ripple Effect
// ============================================================================

class LingjingCardEffects {
  constructor() {
    this.cards = [];
    this.init();
  }

  init() {
    // 初始化涟漪动画样式
    this.injectRippleStyles();

    // 为所有玻璃卡片添加悬停效果
    this.setupCardHoverEffects();

    // 监听 DOM 变化，支持动态添加的卡片（检查浏览器兼容性）
    if (typeof MutationObserver !== 'undefined') {
      this.observeNewCards();
    } else {
      console.warn('当前浏览器不支持 MutationObserver，动态添加的卡片将不会自动获得效果');
    }
  }

  injectRippleStyles() {
    // 检查是否已注入样式
    if (document.getElementById('lingjing-ripple-styles')) return;

    const style = document.createElement('style');
    style.id = 'lingjing-ripple-styles';
    style.textContent = `
      @keyframes lingjing-ripple {
        from {
          transform: translate(-50%, -50%) scale(0);
          opacity: 1;
        }
        to {
          transform: translate(-50%, -50%) scale(4);
          opacity: 0;
        }
      }

      .lingjing-ripple {
        position: absolute;
        border-radius: 50%;
        pointer-events: none;
        animation: lingjing-ripple 0.6s ease-out;
      }
    `;
    document.head.appendChild(style);
  }

  setupCardHoverEffects() {
    // 为所有玻璃卡片类添加涟漪效果
    const selectors = [
      '.card-glass',
      '.glass-card',
      '.glass-flowing',
      '.glass-frosted',
      '.glass-colored'
    ];

    selectors.forEach(selector => {
      const cards = document.querySelectorAll(selector);
      cards.forEach(card => this.attachRippleEffect(card));
    });
  }

  attachRippleEffect(card) {
    // 避免重复添加
    if (card.dataset.lingjingRipple === 'attached') return;

    card.dataset.lingjingRipple = 'attached';

    // 确保卡片有 position 和 overflow 属性
    const computedStyle = window.getComputedStyle(card);
    if (computedStyle.position === 'static') {
      card.style.position = 'relative';
    }
    if (computedStyle.overflow === 'visible') {
      card.style.overflow = 'hidden';
    }

    // 添加鼠标进入事件
    card.addEventListener('mouseenter', (e) => {
      this.createRipple(e, card);
    });
  }

  createRipple(event, element) {
    const rect = element.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    const ripple = document.createElement('div');
    ripple.className = 'lingjing-ripple';

    // 使用深色主题感知的颜色
    const isDarkTheme = document.documentElement.getAttribute('data-theme') === 'dark';
    const rippleColor = isDarkTheme
      ? 'rgba(0, 132, 255, 0.25)'
      : 'rgba(0, 132, 255, 0.3)';

    ripple.style.cssText = `
      width: 100px;
      height: 100px;
      background: radial-gradient(circle, ${rippleColor}, transparent);
      left: ${x}px;
      top: ${y}px;
    `;

    element.appendChild(ripple);

    // 动画结束后移除元素
    setTimeout(() => ripple.remove(), 600);
  }

  observeNewCards() {
    // 使用 MutationObserver 监听 DOM 变化
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === 1) { // Element node
            // 检查新添加的节点是否是卡片
            const selectors = [
              '.card-glass',
              '.glass-card',
              '.glass-flowing',
              '.glass-frosted',
              '.glass-colored'
            ];

            selectors.forEach(selector => {
              if (node.matches && node.matches(selector)) {
                this.attachRippleEffect(node);
              }
              // 检查子元素
              const children = node.querySelectorAll(selector);
              children.forEach(child => this.attachRippleEffect(child));
            });
          }
        });
      });
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }
}

// ============================================================================
// 滚动动画效果 - Scroll Animation
// ============================================================================

class LingjingScrollAnimations {
  constructor() {
    this.init();
  }

  init() {
    this.setupScrollAnimations();
  }

  setupScrollAnimations() {
    const animatedElements = document.querySelectorAll(
      '.card-glass, .glass-card, .glass-flowing, .glass-frosted, .glass-colored'
    );

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry, index) => {
          if (entry.isIntersecting) {
            // 避免重复动画
            if (entry.target.dataset.lingjingAnimated === 'true') return;

            entry.target.dataset.lingjingAnimated = 'true';

            setTimeout(() => {
              entry.target.style.opacity = '1';
              entry.target.style.transform = 'translateY(0)';
            }, index * 50); // 缩短延迟时间，使动画更流畅

            observer.unobserve(entry.target);
          }
        });
      },
      {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
      }
    );

    animatedElements.forEach(element => {
      // 仅为尚未设置动画的元素添加
      if (!element.dataset.lingjingAnimated) {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        element.style.transition = 'opacity 0.6s cubic-bezier(0.2, 0, 0, 1), transform 0.6s cubic-bezier(0.2, 0, 0, 1)';
        observer.observe(element);
      }
    });
  }
}

// ============================================================================
// 主题切换支持 - Theme Support
// ============================================================================

class LingjingThemeManager {
  constructor() {
    this.theme = this.getStoredTheme() || this.getSystemTheme() || 'light';
    this.init();
  }

  init() {
    this.applyTheme(this.theme);
    this.watchSystemTheme();
  }

  getStoredTheme() {
    return localStorage.getItem('lingjing-theme');
  }

  setStoredTheme(theme) {
    localStorage.setItem('lingjing-theme', theme);
  }

  getSystemTheme() {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark';
    }
    return 'light';
  }

  applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    this.theme = theme;
    this.setStoredTheme(theme);
  }

  toggleTheme() {
    const newTheme = this.theme === 'light' ? 'dark' : 'light';
    this.applyTheme(newTheme);
    return newTheme;
  }

  watchSystemTheme() {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

    mediaQuery.addEventListener('change', (e) => {
      // 仅在用户未手动设置主题时应用系统主题
      if (!this.getStoredTheme()) {
        this.applyTheme(e.matches ? 'dark' : 'light');
      }
    });
  }
}

// ============================================================================
// 自动初始化 - Auto Initialize
// ============================================================================

// 当 DOM 加载完成后自动初始化
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initLingjingCore);
} else {
  initLingjingCore();
}

function initLingjingCore() {
  window.Lingjing = window.Lingjing || {};

  // 初始化核心功能
  window.Lingjing.cardEffects = new LingjingCardEffects();
  window.Lingjing.scrollAnimations = new LingjingScrollAnimations();
  window.Lingjing.themeManager = new LingjingThemeManager();

  // 提供全局辅助方法
  window.Lingjing.toggleTheme = () => window.Lingjing.themeManager.toggleTheme();
  window.Lingjing.setTheme = (theme) => window.Lingjing.themeManager.applyTheme(theme);
  window.Lingjing.getTheme = () => window.Lingjing.themeManager.theme;

  console.log('✨ Lingjing Core 交互效果已加载');
}

// 导出类以供外部使用
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    LingjingCardEffects,
    LingjingScrollAnimations,
    LingjingThemeManager
  };
}
