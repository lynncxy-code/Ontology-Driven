/**
 * LingJing Core - B端系统标准交互脚本模板
 *
 * 这个文件包含所有 B 端管理系统常用的交互功能
 * 可以直接复制到项目中使用，无需修改
 *
 * @version 1.0.0
 */

// ============================================
// 1. 移动端侧边栏切换
// ============================================
function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebarOverlay');

  if (sidebar && overlay) {
    sidebar.classList.toggle('active');
    overlay.classList.toggle('active');

    // 阻止页面滚动
    if (sidebar.classList.contains('active')) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
  }
}

// ============================================
// 2. 桌面端侧边栏收起/展开
// ============================================
function toggleSidebarCollapse() {
  const sidebar = document.getElementById('sidebar');

  if (sidebar) {
    sidebar.classList.toggle('collapsed');

    // 保存状态到 localStorage（处理隐私模式异常）
    const isCollapsed = sidebar.classList.contains('collapsed');
    try {
      localStorage.setItem('sidebarCollapsed', isCollapsed);
    } catch (e) {
      console.warn('无法保存侧边栏状态到 localStorage');
    }
  }
}

// 恢复侧边栏收起状态
function restoreSidebarState() {
  const sidebar = document.getElementById('sidebar');
  let savedState = 'false';
  try {
    savedState = localStorage.getItem('sidebarCollapsed');
  } catch (e) {
    console.warn('无法从 localStorage 读取侧边栏状态');
  }

  if (sidebar && savedState === 'true') {
    sidebar.classList.add('collapsed');
  }
}

// ============================================
// 3. 主题切换
// ============================================
function initTheme() {
  const html = document.documentElement;
  const savedTheme = localStorage.getItem('theme') || 'light';

  html.setAttribute('data-theme', savedTheme);
}

function toggleTheme() {
  const html = document.documentElement;
  const currentTheme = html.getAttribute('data-theme');
  const newTheme = currentTheme === 'light' ? 'dark' : 'light';

  html.setAttribute('data-theme', newTheme);
  localStorage.setItem('theme', newTheme);

  // 触发自定义事件
  window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme: newTheme } }));
}

// 全局主题切换方法
window.Lingjing = window.Lingjing || {};
window.Lingjing.toggleTheme = toggleTheme;

// ============================================
// 4. 导航链接激活状态管理
// ============================================
function initNavigation() {
  const navLinks = document.querySelectorAll('.b-sidebar-nav-link');

  navLinks.forEach(link => {
    link.addEventListener('click', function(e) {
      // 移除所有激活状态
      navLinks.forEach(l => l.classList.remove('active'));

      // 添加当前激活状态
      this.classList.add('active');

      // 移动端：点击后自动关闭侧边栏
      if (window.innerWidth < 768) {
        toggleSidebar();
      }
    });
  });
}

// ============================================
// 5. 数据表格交互
// ============================================

// 表格行选择
function initTableSelection() {
  const checkboxes = document.querySelectorAll('.data-table tbody input[type="checkbox"]');
  const selectAll = document.querySelector('.data-table thead input[type="checkbox"]');

  if (selectAll) {
    selectAll.addEventListener('change', function() {
      checkboxes.forEach(checkbox => {
        checkbox.checked = this.checked;
      });
      updateSelectedCount();
    });
  }

  checkboxes.forEach(checkbox => {
    checkbox.addEventListener('change', function() {
      updateSelectedCount();

      // 更新全选框状态
      if (selectAll) {
        const allChecked = Array.from(checkboxes).every(cb => cb.checked);
        const someChecked = Array.from(checkboxes).some(cb => cb.checked);
        selectAll.checked = allChecked;
        selectAll.indeterminate = someChecked && !allChecked;
      }
    });
  });
}

// 更新选中数量显示
function updateSelectedCount() {
  const checkboxes = document.querySelectorAll('.data-table tbody input[type="checkbox"]:checked');
  const count = checkboxes.length;

  // 触发自定义事件
  window.dispatchEvent(new CustomEvent('selectionChanged', { detail: { count } }));

  console.log(`已选中 ${count} 项`);
}

// ============================================
// 6. 搜索和筛选
// ============================================

// 搜索防抖
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// 初始化搜索
function initSearch() {
  const searchInput = document.querySelector('.search-input');

  if (searchInput) {
    const debouncedSearch = debounce((value) => {
      console.log('搜索:', value);
      // 这里添加实际的搜索逻辑
      performSearch(value);
    }, 300);

    searchInput.addEventListener('input', (e) => {
      debouncedSearch(e.target.value);
    });
  }
}

// 执行搜索（需要自定义实现）
function performSearch(keyword) {
  // 示例：触发自定义事件
  window.dispatchEvent(new CustomEvent('search', { detail: { keyword } }));
}

// 初始化筛选
function initFilters() {
  const filterSelects = document.querySelectorAll('.filter-select');

  filterSelects.forEach(select => {
    select.addEventListener('change', (e) => {
      console.log('筛选:', e.target.value);
      performFilter();
    });
  });
}

// 执行筛选（需要自定义实现）
function performFilter() {
  const filters = {};

  document.querySelectorAll('.filter-select').forEach(select => {
    if (select.value) {
      filters[select.name || 'filter'] = select.value;
    }
  });

  // 触发自定义事件
  window.dispatchEvent(new CustomEvent('filter', { detail: { filters } }));
}

// ============================================
// 7. 分页功能
// ============================================
function initPagination() {
  const paginationButtons = document.querySelectorAll('.pagination button:not([disabled])');

  paginationButtons.forEach(button => {
    button.addEventListener('click', function() {
      const page = this.textContent.trim();

      if (page && !isNaN(page)) {
        goToPage(parseInt(page));
      } else if (this.querySelector('i[data-lucide="chevron-left"]')) {
        goToPreviousPage();
      } else if (this.querySelector('i[data-lucide="chevron-right"]')) {
        goToNextPage();
      }
    });
  });
}

// 跳转到指定页（需要自定义实现）
function goToPage(page) {
  console.log('跳转到第', page, '页');

  // 更新激活状态
  document.querySelectorAll('.pagination button').forEach(btn => {
    btn.classList.remove('active');
    if (btn.textContent.trim() === page.toString()) {
      btn.classList.add('active');
    }
  });

  // 触发自定义事件
  window.dispatchEvent(new CustomEvent('pageChanged', { detail: { page } }));
}

function goToPreviousPage() {
  const currentPage = parseInt(document.querySelector('.pagination button.active')?.textContent);
  if (currentPage && currentPage > 1) {
    goToPage(currentPage - 1);
  }
}

function goToNextPage() {
  const currentPage = parseInt(document.querySelector('.pagination button.active')?.textContent);
  const lastPage = parseInt([...document.querySelectorAll('.pagination button')].pop()?.textContent);

  if (currentPage && lastPage && currentPage < lastPage) {
    goToPage(currentPage + 1);
  }
}

// ============================================
// 8. 表单验证（简单示例）
// ============================================
function validateForm(formElement) {
  const inputs = formElement.querySelectorAll('input[required], select[required], textarea[required]');
  let isValid = true;

  inputs.forEach(input => {
    if (!input.value.trim()) {
      isValid = false;
      input.classList.add('input-error');
      showFieldError(input, '此字段为必填项');
    } else {
      input.classList.remove('input-error');
      hideFieldError(input);
    }
  });

  return isValid;
}

function showFieldError(input, message) {
  let errorElement = input.nextElementSibling;

  if (!errorElement || !errorElement.classList.contains('field-error')) {
    errorElement = document.createElement('div');
    errorElement.className = 'field-error';
    input.parentNode.insertBefore(errorElement, input.nextSibling);
  }

  errorElement.textContent = message;
  errorElement.style.display = 'block';
}

function hideFieldError(input) {
  const errorElement = input.nextElementSibling;

  if (errorElement && errorElement.classList.contains('field-error')) {
    errorElement.style.display = 'none';
  }
}

// ============================================
// 9. Toast 通知（简单实现）
// ============================================
function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;

  // 简单样式
  toast.style.cssText = `
    position: fixed;
    top: 80px;
    right: 20px;
    padding: 12px 20px;
    background: var(--bg-card);
    border: 1px solid var(--theme-border-base);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-lg);
    z-index: 9999;
    animation: slideInRight 0.3s ease;
  `;

  document.body.appendChild(toast);

  // 3秒后自动移除
  setTimeout(() => {
    toast.style.animation = 'slideOutRight 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// ============================================
// 10. 确认对话框（简单实现）
// ============================================
function showConfirm(message, onConfirm, onCancel) {
  const confirmed = confirm(message);

  if (confirmed && onConfirm) {
    onConfirm();
  } else if (!confirmed && onCancel) {
    onCancel();
  }

  return confirmed;
}

// ============================================
// 11. Loading 状态管理
// ============================================
function showLoading() {
  const loading = document.createElement('div');
  loading.id = 'globalLoading';
  loading.innerHTML = `
    <div style="position: fixed; inset: 0; background: rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center; z-index: 99999;">
      <div style="background: var(--bg-card); padding: 20px; border-radius: var(--radius-lg); box-shadow: var(--shadow-lg);">
        <div class="spinner"></div>
        <div style="margin-top: 10px; color: var(--text-primary);">加载中...</div>
      </div>
    </div>
  `;

  document.body.appendChild(loading);
}

function hideLoading() {
  const loading = document.getElementById('globalLoading');
  if (loading) {
    loading.remove();
  }
}

// ============================================
// 12. 响应式监听
// ============================================
function handleResize() {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebarOverlay');

  // 桌面端自动关闭移动端菜单
  if (window.innerWidth >= 768) {
    if (sidebar) sidebar.classList.remove('active');
    if (overlay) overlay.classList.remove('active');
    document.body.style.overflow = '';
  }

  // 桌面端自动展开侧边栏
  if (window.innerWidth >= 1024) {
    if (sidebar && sidebar.classList.contains('collapsed')) {
      const savedState = localStorage.getItem('sidebarCollapsed');
      if (savedState !== 'true') {
        sidebar.classList.remove('collapsed');
      }
    }
  }
}

// 防抖处理 resize 事件
const debouncedResize = debounce(handleResize, 250);
window.addEventListener('resize', debouncedResize);

// ============================================
// 初始化
// ============================================
document.addEventListener('DOMContentLoaded', function() {
  console.log('✅ LingJing Core B端交互脚本加载完成');

  // 1. 初始化主题
  initTheme();

  // 2. 恢复侧边栏状态
  restoreSidebarState();

  // 3. 初始化导航
  initNavigation();

  // 4. 初始化表格选择
  initTableSelection();

  // 5. 初始化搜索
  initSearch();

  // 6. 初始化筛选
  initFilters();

  // 7. 初始化分页
  initPagination();

  // 8. 初始化 Lucide 图标（如果引入了）
  if (typeof lucide !== 'undefined') {
    lucide.createIcons();
  }

  // 9. 主题变化时重新渲染图标
  window.addEventListener('themeChanged', () => {
    if (typeof lucide !== 'undefined') {
      lucide.createIcons();
    }
  });
});

// ============================================
// 导出全局方法
// ============================================
window.LingJingB = {
  // 侧边栏
  toggleSidebar,
  toggleSidebarCollapse,

  // 主题
  toggleTheme,

  // 通知
  showToast,
  showConfirm,

  // Loading
  showLoading,
  hideLoading,

  // 表单
  validateForm,

  // 分页
  goToPage,
  goToPreviousPage,
  goToNextPage,

  // 搜索筛选
  performSearch,
  performFilter
};

console.log('📦 LingJing Core B端交互脚本 v1.0.0');
console.log('🌐 全局方法: window.LingJingB');
