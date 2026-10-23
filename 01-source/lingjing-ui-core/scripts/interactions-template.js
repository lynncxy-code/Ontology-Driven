/**
 * LingJing Core - 标准交互脚本模板
 *
 * 这个文件包含所有网站常用的交互功能
 * 可以直接复制到项目中使用，无需修改
 *
 * @version 1.0.0
 */

// ============================================
// 1. 主题切换
// ============================================
const themeToggle = document.getElementById('themeToggle');
const html = document.documentElement;

// 读取本地保存的主题（处理隐私模式异常）
let savedTheme = 'light';
try {
  savedTheme = localStorage.getItem('theme') || 'light';
} catch (e) {
  console.warn('无法访问 localStorage，使用默认主题');
}
html.setAttribute('data-theme', savedTheme);

// 主题切换事件
if (themeToggle) {
  themeToggle.addEventListener('click', () => {
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    html.setAttribute('data-theme', newTheme);
    try {
      localStorage.setItem('theme', newTheme);
    } catch (e) {
      console.warn('无法保存主题到 localStorage');
    }
  });
}

// ============================================
// 2. 导航栏滚动效果（带节流）
// ============================================
const navbar = document.getElementById('navbar');
let lastScrollTop = 0;
let ticking = false;

window.addEventListener('scroll', () => {
  if (!ticking) {
    window.requestAnimationFrame(() => {
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

      // 滚动超过 50px 添加 scrolled 类
      if (navbar) {
        if (scrollTop > 50) {
          navbar.classList.add('scrolled');
        } else {
          navbar.classList.remove('scrolled');
        }
      }

      lastScrollTop = scrollTop;
      ticking = false;
    });
    ticking = true;
  }
});

// ============================================
// 3. 导航链接激活状态
// ============================================
const sections = document.querySelectorAll('section[id]');
const navLinks = document.querySelectorAll('.website-nav-link');

window.addEventListener('scroll', () => {
  let current = '';

  sections.forEach(section => {
    const sectionTop = section.offsetTop;
    const sectionHeight = section.clientHeight;

    if (window.pageYOffset >= sectionTop - 100) {
      current = section.getAttribute('id');
    }
  });

  navLinks.forEach(link => {
    link.classList.remove('active');
    if (link.getAttribute('href') === `#${current}`) {
      link.classList.add('active');
    }
  });
});

// ============================================
// 4. 平滑滚动
// ============================================
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function(e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));

    if (target) {
      const offsetTop = target.offsetTop - 80;
      window.scrollTo({
        top: offsetTop,
        behavior: 'smooth'
      });
    }
  });
});

// ============================================
// 5. 滚动入场动画
// ============================================
const observerOptions = {
  threshold: 0.1,
  rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.style.opacity = '1';
      entry.target.style.transform = 'translateY(0)';
    }
  });
}, observerOptions);

// 为卡片添加入场动画
const animatedElements = document.querySelectorAll('.website-solution-card, .website-product-card, .website-tech-card');
animatedElements.forEach(element => {
  element.style.opacity = '0';
  element.style.transform = 'translateY(20px)';
  element.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
  observer.observe(element);
});

// ============================================
// 6. 鼠标涟漪效果
// ============================================
function createRipple(event, element) {
  const rect = element.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;

  const ripple = document.createElement('div');
  ripple.className = 'card-ripple-effect';
  ripple.style.cssText = `
    position: absolute;
    width: 100px;
    height: 100px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(0, 132, 255, 0.3), transparent);
    left: ${x}px;
    top: ${y}px;
    transform: translate(-50%, -50%) scale(0);
    animation: card-ripple 0.6s ease-out;
    pointer-events: none;
    z-index: 0;
  `;

  element.appendChild(ripple);

  setTimeout(() => ripple.remove(), 600);
}

// 为所有卡片添加鼠标涟漪效果
const rippleCards = document.querySelectorAll('.website-solution-card, .website-product-card, .website-tech-card');
rippleCards.forEach(card => {
  card.addEventListener('mouseenter', (e) => {
    createRipple(e, card);
  });
});

// ============================================
// 7. 移动端菜单（可选）
// ============================================
const mobileMenuToggle = document.getElementById('mobileMenuToggle');
const mobileMenu = document.querySelector('.website-nav-links');

if (mobileMenuToggle && mobileMenu) {
  mobileMenuToggle.addEventListener('click', () => {
    mobileMenu.classList.toggle('active');
    mobileMenuToggle.classList.toggle('active');
  });
}

// ============================================
// 8. 表单验证（可选）
// ============================================
const forms = document.querySelectorAll('form');

forms.forEach(form => {
  form.addEventListener('submit', (e) => {
    e.preventDefault();

    // 这里添加你的表单提交逻辑
    console.log('表单提交');
  });
});

// ============================================
// 9. 页面加载完成提示
// ============================================
console.log('✅ LingJing Core 交互脚本加载完成');
console.log('📦 版本: 1.0.0');
console.log('🎨 主题: ' + savedTheme);
