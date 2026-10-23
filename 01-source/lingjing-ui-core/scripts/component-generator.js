/**
 * LingJing Core - 组件生成器 v3.0
 *
 * 功能：
 * - 根据配置生成组件代码
 * - 支持自定义配置
 * - 支持组件组合
 * - 代码验证和优化
 */

class ComponentGenerator {
  constructor(config) {
    this.config = config || this.loadConfig();
  }

  /**
   * 加载组件配置
   */
  loadConfig() {
    // 从 data/component-config.json 加载配置
    return window.COMPONENT_CONFIG || {};
  }

  /**
   * 生成组件
   * @param {string} componentName - 组件名称
   * @param {object} options - 组件选项
   * @returns {string} HTML 代码
   */
  generate(componentName, options = {}) {
    const component = this.config.components[componentName];

    if (!component) {
      console.error(`组件 "${componentName}" 不存在`);
      return '';
    }

    return this.buildComponent(component, { ...options, componentName });
  }


  /**
   * 构建组件 HTML
   * @param {object} component - 组件配置
   * @param {object} options - 组件选项
   * @returns {string} HTML 代码
   */
  buildComponent(component, options) {
    let html = '';
    const componentName = options.componentName || '';

    switch (componentName) {
      case 'button':
        html = this.buildButton(component, options);
        break;
      case 'card':
        html = this.buildCard(component, options);
        break;
      case 'input':
        html = this.buildInput(component, options);
        break;
      case 'table':
        html = this.buildTable(component, options);
        break;
      case 'badge':
        html = this.buildBadge(component, options);
        break;
      case 'drawer':
        html = this.buildDrawer(component, options);
        break;
      case 'accordion':
        html = this.buildAccordion(component, options);
        break;
      case 'stepper':
        html = this.buildStepper(component, options);
        break;
      case 'segmented-control':
        html = this.buildSegmentedControl(component, options);
        break;
      case 'popover':
        html = this.buildPopover(component, options);
        break;
      case 'empty-state':
        html = this.buildEmptyState(component, options);
        break;
      case 'skeleton':
        html = this.buildSkeleton(component, options);
        break;
      case 'status-dot':
        html = this.buildStatusDot(component, options);
        break;
      case 'chat-layout':
        html = this.buildChatLayout(component, options);
        break;
      case 'message-bubble':
        html = this.buildMessageBubble(component, options);
        break;
      case 'agent-thinking':
        html = this.buildAgentThinking(component, options);
        break;
      case 'tool-call':
        html = this.buildToolCall(component, options);
        break;
      case 'task-status-card':
        html = this.buildTaskStatusCard(component, options);
        break;
      case 'advanced-data-table':
        html = this.buildAdvancedDataTable(component, options);
        break;
      case 'filter-panel':
        html = this.buildFilterPanel(component, options);
        break;
      case 'detail-panel':
        html = this.buildDetailPanel(component, options);
        break;
      case 'flight-metric-card':
        html = this.buildFlightMetricCard(component, options);
        break;
      case 'route-leg-card':
        html = this.buildRouteLegCard(component, options);
        break;
      case 'mission-status-board':
        html = this.buildMissionStatusBoard(component, options);
        break;
      case 'chart-card':
        html = this.buildChartCard(component, options);
        break;
      case 'metric-trend':
        html = this.buildMetricTrend(component, options);
        break;
      case 'progress-ring':
        html = this.buildProgressRing(component, options);
        break;
      case 'timeline-strip':
        html = this.buildTimelineStrip(component, options);
        break;
      default:
        html = this.buildGeneric(component, options);

    }

    return html;
  }

  /**
   * 构建抽屉组件
   */
  buildDrawer(component, options) {
    const { position = 'right', title = '抽屉标题', content = '内容...' } = options;
    return `<div class="feedback-drawer feedback-drawer-${position}">
  <div class="feedback-drawer-header">
    <span class="feedback-drawer-title">${title}</span>
    <button class="feedback-drawer-close"><i data-lucide="x"></i></button>
  </div>
  <div class="feedback-drawer-body">${content}</div>
  <div class="feedback-drawer-footer">
    <button class="btn-outline">取消</button>
    <button class="btn-primary">确定</button>
  </div>
</div>`;
  }

  /**
   * 构建手风琴组件
   */
  buildAccordion(component, options) {
    const { items = [{ title: '面板 1', content: '内容 1...', active: true }] } = options;
    let html = '<div class="data-accordion">';
    items.forEach(item => {
      html += `
  <div class="data-accordion-item ${item.active ? 'active' : ''}">
    <button class="data-accordion-header">
      <span>${item.title}</span>
      <i data-lucide="chevron-down" class="data-accordion-icon"></i>
    </button>
    <div class="data-accordion-content">
      <div class="data-accordion-body">${item.content}</div>
    </div>
  </div>`;
    });
    html += '</div>';
    return html;
  }

  /**
   * 构建步骤条组件
   */
  buildStepper(component, options) {
    const { variant = 'horizontal', steps = [
      { title: '第一步', status: 'completed' },
      { title: '第二步', status: 'active' },
      { title: '第三步', status: 'pending' }
    ] } = options;
    
    let html = `<div class="stepper-${variant}">`;
    steps.forEach((step, index) => {
      html += `
  <div class="stepper-step ${step.status}">
    <div class="stepper-step-header">
      <div class="stepper-step-icon">${step.status === 'completed' ? '<i data-lucide="check" style="width:16px;height:16px;"></i>' : index + 1}</div>
      ${index < steps.length - 1 ? '<div class="stepper-step-connector"></div>' : ''}
    </div>
    <div class="stepper-step-content">
      <div class="stepper-step-title">${step.title}</div>
    </div>
  </div>`;
    });
    html += '</div>';
    return html;
  }

  /**
   * 构建分段控制组件
   */
  buildSegmentedControl(component, options) {
    const { items = ['选项 A', '选项 B', '选项 C'], activeIndex = 0 } = options;
    let html = '<div class="segmented-control">';
    items.forEach((item, index) => {
      html += `<div class="segmented-control-item ${index === activeIndex ? 'active' : ''}">${item}</div>`;
    });
    html += '</div>';
    return html;
  }

  /**
   * 构建气泡卡片组件
   */
  buildPopover(component, options) {
    const { position = 'top', title = '气泡标题', content = '详细内容...' } = options;
    return `<div class="popover-container active">
  <button class="btn-outline">悬浮我</button>
  <div class="popover-content popover-${position}">
    <div class="popover-title">${title}</div>
    <div class="popover-body">${content}</div>
    <div class="popover-arrow"></div>
  </div>
</div>`;
  }

  /**
   * 构建空状态组件
   */
  buildEmptyState(component, options) {
    const { icon = 'folder-open', title = '暂无数据', description = '当前没有任何记录' } = options;
    return `<div class="empty-state">
  <div class="empty-state-icon"><i data-lucide="${icon}"></i></div>
  <div class="empty-state-title">${title}</div>
  <div class="empty-state-description">${description}</div>
</div>`;
  }

  /**
   * 构建状态圆点组件
   */
  buildStatusDot(component, options) {
    const { variant = 'success', text = '运行中' } = options;
    return `<span class="status-dot status-dot-${variant}">${text}</span>`;
  }


  /**
   * 构建按钮组件
   */
  buildButton(component, options) {
    const {
      variant = 'primary',
      size = 'md',
      text = '按钮',
      icon = null,
      loading = false,
      disabled = false,
      onClick = null
    } = options;

    let className = component.cssClass[0];

    // 添加变体
    if (variant) {
      className = `${className}-${variant}`;
    }

    // 添加尺寸
    if (size && size !== 'md') {
      className += ` btn-${size}`;
    }

    // 添加状态
    if (loading) className += ' loading';
    if (disabled) className += ' disabled';

    // 构建 HTML
    let html = `<button class="${className}"`;

    if (disabled) html += ' disabled';
    if (onClick) html += ` onclick="${onClick}"`;
    if (loading) html += ' data-loading';

    html += '>';

    // 图标
    if (icon) {
      html += `<i data-lucide="${icon}"></i>`;
    }

    // 加载图标
    if (loading) {
      html += `<i data-lucide="loader-2" class="loading-icon"></i>`;
    }

    // 文本
    if (text) {
      html += `<span>${text}</span>`;
    }

    html += '</button>';

    return html;
  }

  /**
   * 构建卡片组件
   */
  buildCard(component, options) {
    const {
      variant = 'default',
      title = null,
      content = '',
      footer = null,
      actions = null
    } = options;

    let className = component.cssClass[0];

    // 添加变体
    if (variant !== 'default') {
      className = variant === 'glass' ? 'presentation-glass-card' : `${className}-${variant}`;
    }

    let html = `<div class="${className}">`;

    // 标题
    if (title) {
      html += `<h3>${title}</h3>`;
    }

    // 内容
    if (content) {
      html += content;
    }

    // 底部
    if (footer || actions) {
      html += '<div class="card-footer">';

      if (actions) {
        html += '<div class="action-buttons">';
        actions.forEach(action => {
          html += this.generate('button', action);
        });
        html += '</div>';
      }

      if (footer) {
        html += footer;
      }

      html += '</div>';
    }

    html += '</div>';

    return html;
  }

  /**
   * 构建输入框组件
   */
  buildInput(component, options) {
    const {
      type = 'text',
      placeholder = '',
      value = '',
      disabled = false,
      label = null,
      error = null
    } = options;

    let className = component.cssClass[0];

    let html = '';

    // 标签
    if (label) {
      html += `<label class="form-label">${label}</label>`;
    }

    // 输入框
    html += `<input type="${type}" class="${className}"`;

    if (placeholder) html += ` placeholder="${placeholder}"`;
    if (value) html += ` value="${value}"`;
    if (disabled) html += ' disabled';

    html += ' />';

    // 错误信息
    if (error) {
      html += `<span class="error-message">${error}</span>`;
    }

    return html;
  }

  /**
   * 构建表格组件
   */
  buildTable(component, options) {
    const {
      headers = [],
      rows = [],
      striped = false
    } = options;

    let className = component.cssClass;

    if (striped) className += ' table-striped';

    let html = `<table class="${className}"><thead><tr>`;

    // 表头
    headers.forEach(header => {
      html += `<th>${header}</th>`;
    });
    html += '</tr></thead><tbody>';

    // 表格内容
    rows.forEach(row => {
      html += '<tr>';
      row.forEach(cell => {
        html += `<td>${cell}</td>`;
      });
      html += '</tr>';
    });

    html += '</tbody></table>';

    return html;
  }

  /**
   * 构建徽章组件
   */
  buildBadge(component, options) {
    const {
      variant = 'primary',
      text = 'Badge',
      size = 'md'
    } = options;

    let className = component.cssClass;

    if (variant) className += ` ${variant}`;
    if (size === 'sm') className += ' badge-sm';

    return `<span class="${className}">${text}</span>`;
  }

  /**
   * 构建通用组件
   */
  buildGeneric(component, options) {
    // 从示例中获取模板
    const example = component.examples[Object.keys(component.examples)[0]];
    return example || `<div class="${component.cssClass}">Component</div>`;
  }

  /**
   * 生成组件组合
   * @param {string} combinationName - 组合名称
   * @param {object} data - 组件数据
   * @returns {string} HTML 代码
   */
  combine(combinationName, data = {}) {
    const combination = this.config.combinations[combinationName];

    if (!combination) {
      console.error(`组合 "${combinationName}" 不存在`);
      return '';
    }

    let html = combination.template;

    // 替换占位符
    Object.keys(data).forEach(key => {
      const placeholder = `{${key}}`;
      html = html.replace(new RegExp(placeholder, 'g'), data[key]);
    });

    return html;
  }

  /**
   * 批量生成组件
   * @param {array} items - 组件列表
   * @returns {string} HTML 代码
   */
  generateBatch(items) {
    return items.map(item => {
      return this.generate(item.component, item.options);
    }).join('\n');
  }

  /**
   * 验证组件配置
   * @param {string} componentName - 组件名称
   * @param {object} options - 组件选项
   * @returns {object} 验证结果
   */
  validate(componentName, options) {
    const component = this.config.components[componentName];

    if (!component) {
      return {
        valid: false,
        errors: [`组件 "${componentName}" 不存在`]
      };
    }

    const errors = [];

    // 验证变体
    if (options.variant && !component.variants.includes(options.variant)) {
      errors.push(`变体 "${options.variant}" 不支持`);
    }

    // 验证尺寸
    if (options.size && !component.sizes.includes(options.size)) {
      errors.push(`尺寸 "${options.size}" 不支持`);
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }

  /**
   * 获取组件配置
   * @param {string} componentName - 组件名称
   * @returns {object} 组件配置
   */
  getComponentConfig(componentName) {
    return this.config.components[componentName] || null;
  }

  /**
   * 获取所有组件列表
   * @returns {array} 组件列表
   */
  getAllComponents() {
    return Object.keys(this.config.components).map(name => ({
      name,
      ...this.config.components[name]
    }));
  }

  /**
   * 构建骨架屏组件
   */
  buildSkeleton(component, options) {
    return `<div style="width: 100%; max-width: 400px;">
  <div class="skeleton skeleton-title" style="width: 40%; margin-bottom: 12px;"></div>
  <div class="skeleton skeleton-text" style="margin-bottom: 8px;"></div>
  <div class="skeleton skeleton-text" style="margin-bottom: 8px;"></div>
  <div class="skeleton skeleton-text" style="width: 60%;"></div>
</div>`;
  }

  /**
   * 构建对话布局
   */
  buildChatLayout(component, options) {
    const { messages = '' } = options;
    return `
<div class="chat-layout">
  <div class="chat-messages">
    ${messages || `
      ${this.buildMessageBubble({}, { variant: 'assistant', text: '你好！我是灵境 AI 助手，有什么可以帮您的？' })}
      ${this.buildMessageBubble({}, { variant: 'user', text: '请帮我查询当前的飞行计划。' })}
      ${this.buildAgentThinking()}
    `}
  </div>
  <div class="chat-input-area">
    <div class="chat-input-wrapper">
      <textarea class="chat-input" placeholder="输入您的问题..."></textarea>
      <div class="chat-input-actions">
        <div style="display: flex; gap: var(--spacing-sm);">
          <button class="btn-icon"><i data-lucide="paperclip" style="width:18px;height:18px;"></i></button>
          <button class="btn-icon"><i data-lucide="image" style="width:18px;height:18px;"></i></button>
        </div>
        <button class="btn-primary btn-sm">发送</button>
      </div>
    </div>
  </div>
</div>`;
  }

  /**
   * 构建消息气泡
   */
  buildMessageBubble(component, options) {
    const { variant = 'assistant', text = '消息内容' } = options;
    const isUser = variant === 'user';
    return `
<div class="message-bubble ${isUser ? 'message-bubble-user' : 'message-bubble-ai'}">
  <div class="message-avatar ${isUser ? 'message-avatar-user' : 'message-avatar-ai'}">
    <i data-lucide="${isUser ? 'user' : 'bot'}"></i>
  </div>
  <div class="message-content">
    <div class="message-text">${text}</div>
  </div>
</div>`;
  }

  /**
   * 构建思考状态
   */
  buildAgentThinking(component, options) {
    return `
<div class="agent-thinking">
  <div class="thinking-dot"></div>
  <div class="thinking-dot"></div>
  <div class="thinking-dot"></div>
  <span>AI 正在思考...</span>
</div>`;
  }

  /**
   * 构建工具调用
   */
  buildToolCall(component, options) {
    const { tool = 'getFlightPlan', status = 'success' } = options;
    return `
<div class="tool-call-card">
  <div class="tool-call-status tool-call-status-${status}"></div>
  <i data-lucide="terminal" style="width:14px;height:14px;"></i>
  <span>正在调用 <strong>${tool}</strong>...</span>
</div>`;
  }

  /**
   * 构建任务进度卡片
   */
  buildTaskStatusCard(component, options) {
    const { title = '正在处理任务', percent = 45 } = options;
    return `
<div class="task-status-card">
  <div class="task-status-header">
    <span class="task-status-title">${title}</span>
    <span class="badge info">${percent}%</span>
  </div>
  <div class="task-progress">
    <div class="task-progress-inner" style="width: ${percent}%"></div>
  </div>
</div>`;
  }

  /**
   * 构建高级数据表格
   */
  buildAdvancedDataTable(component, options) {
    const { sideContent = '' } = options;
    return `
<div class="advanced-data-table">
  <div class="advanced-data-table-main">
    <div class="table-toolbar">
      <div class="table-toolbar-main">
        <input type="text" class="search-input" placeholder="搜索关键词..." style="max-width: 240px;">
        <button class="btn-outline btn-sm"><i data-lucide="filter" style="width:14px;height:14px;"></i>筛选</button>
      </div>
      <div class="table-toolbar-actions">
        <button class="btn-primary btn-sm">新建任务</button>
      </div>
    </div>
    <div class="data-table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>任务名称</th>
            <th>状态</th>
            <th>进度</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>#8291</td>
            <td>北京-上海航路优化</td>
            <td><span class="status-dot status-dot-processing">处理中</span></td>
            <td>85%</td>
            <td><button class="btn-text btn-sm">查看</button></td>
          </tr>
          <tr>
            <td>#8290</td>
            <td>燃油经济性分析</td>
            <td><span class="status-dot status-dot-success">已完成</span></td>
            <td>100%</td>
            <td><button class="btn-text btn-sm">报告</button></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
  <div class="advanced-data-table-side">
    ${sideContent || this.buildDetailPanel({}, { title: '任务详情' })}
  </div>
</div>`;
  }

  /**
   * 构建筛选面板
   */
  buildFilterPanel(component, options) {
    return `
<div class="filter-panel">
  <div class="filter-panel-header">
    <span class="filter-panel-title">高级筛选</span>
    <button class="btn-text" style="font-size: var(--font-size-xs);">清除</button>
  </div>
  <div class="filter-panel-body">
    <div class="form-group">
      <label class="form-label">日期范围</label>
      <input type="date" class="form-input">
    </div>
    <div class="form-group">
      <label class="form-label">优先级</label>
      <select class="form-select">
        <option>全部</option>
        <option>高</option>
        <option>中</option>
        <option>低</option>
      </select>
    </div>
  </div>
  <div class="filter-panel-footer">
    <button class="btn-primary" style="width: 100%;">确认筛选</button>
  </div>
</div>`;
  }

  /**
   * 构建详情面板
   */
  buildDetailPanel(component, options) {
    const { title = '详情信息' } = options;
    return `
<div class="detail-panel">
  <div class="detail-panel-header">
    <div class="detail-panel-title">${title}</div>
    <div class="badge info">待处理</div>
  </div>
  <div class="detail-section">
    <div class="detail-section-title">基础资料</div>
    <div class="detail-grid">
      <div class="detail-item">
        <div class="detail-label">创建人</div>
        <div class="detail-value">张三</div>
      </div>
      <div class="detail-item">
        <div class="detail-label">时间</div>
        <div class="detail-value">2026-03-19</div>
      </div>
    </div>
  </div>
  <div class="detail-section">
    <div class="detail-section-title">执行进度</div>
    <div class="status-timeline">
      <div class="status-timeline-item completed">
        <div class="status-timeline-dot"></div>
        <div class="status-timeline-content">
          <div class="status-timeline-title">提交申请</div>
          <div class="status-timeline-time">10:00</div>
        </div>
      </div>
      <div class="status-timeline-item">
        <div class="status-timeline-dot"></div>
        <div class="status-timeline-content">
          <div class="status-timeline-title">方案审核</div>
          <div class="status-timeline-time">进行中</div>
        </div>
      </div>
    </div>
  </div>
</div>`;
  }

  /**
   * 构建航空指标卡
   */
  buildFlightMetricCard(component, options) {
    const { title = '执行中航班', value = '1,452', trend = '+12.5%', status = 'up' } = options;
    return `<div class="flight-metric-card">
  <div class="flight-metric-header">
    <h4 class="flight-metric-title">${title}</h4>
    <span class="flight-metric-chip">REALTIME</span>
  </div>
  <div class="flight-metric-value">${value}</div>
  <div class="flight-metric-meta">
    <span class="flight-metric-trend ${status}">${trend} <i data-lucide="trending-${status}"></i></span>
    <span>较昨日增长</span>
  </div>
</div>`;
  }

  /**
   * 构建航段卡片
   */
  buildRouteLegCard(component, options) {
    const { from = 'PEK', to = 'SHA', status = 'on-time', info = '已准点起飞' } = options;
    return `<div class="route-leg-card">
  <div class="route-leg-location">
    <span class="route-leg-code">${from}</span>
    <span class="route-leg-label">Beijing</span>
  </div>
  <div class="route-leg-divider"></div>
  <div class="route-leg-location">
    <span class="route-leg-code">${to}</span>
    <span class="route-leg-label">Shanghai</span>
  </div>
  <div class="route-leg-status">
    <span class="route-leg-badge ${status}">${status.toUpperCase()}</span>
    <span>${info}</span>
  </div>
</div>`;
  }

  /**
   * 构建任务状态板
   */
  buildMissionStatusBoard(component, options) {
    const { title = '关键任务监控' } = options;
    return `<div class="mission-status-board">
  <div class="mission-status-header">
    <h3 class="mission-status-title">${title}</h3>
    <span class="mission-status-meta">6 Active Tasks</span>
  </div>
  <div class="mission-status-list">
    <div class="mission-status-item">
      <div class="mission-status-dot success"></div>
      <div class="mission-status-content">
        <div class="mission-status-name">航路流量分析 (Route-01)</div>
        <div class="mission-status-desc">分析引擎正在计算最佳偏移航线...</div>
      </div>
    </div>
    <div class="mission-status-item">
      <div class="mission-status-dot"></div>
      <div class="mission-status-content">
        <div class="mission-status-name">燃油配载复核 (Fuel-Scan)</div>
        <div class="mission-status-desc">待负责人审批确认...</div>
      </div>
    </div>
  </div>
</div>`;
  }

  /**
   * 构建图表卡片
   */
  buildChartCard(component, options) {
    const { title = '统计分析' } = options;
    return `<div class="chart-card">
  <div class="chart-card-header">
    <h3 class="chart-card-title">${title}</h3>
    <div class="chart-card-actions">
      <button class="btn-ghost btn-sm"><i data-lucide="more-horizontal"></i></button>
    </div>
  </div>
  <div class="chart-card-body">
    <div style="height: 160px; display: flex; align-items: flex-end; gap: 8px; padding: 20px 0;">
      <div style="flex:1; background: var(--theme-primary); opacity: 0.3; height: 40%; border-radius: 4px;"></div>
      <div style="flex:1; background: var(--theme-primary); opacity: 0.6; height: 70%; border-radius: 4px;"></div>
      <div style="flex:1; background: var(--theme-primary); opacity: 0.4; height: 55%; border-radius: 4px;"></div>
      <div style="flex:1; background: var(--theme-primary); opacity: 0.8; height: 90%; border-radius: 4px;"></div>
      <div style="flex:1; background: var(--theme-primary); height: 65%; border-radius: 4px;"></div>
    </div>
  </div>
</div>`;
  }

  /**
   * 构建指标趋势
   */
  buildMetricTrend(component, options) {
    const { value = '96%', label = '安全指数', progress = '72%' } = options;
    return `<div class="metric-trend" style="background: var(--bg-card); padding: 16px; border-radius: 12px; border: 1px solid var(--glass-border-light);">
  <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
    <span style="font-size: 14px; color: var(--text-secondary);">${label}</span>
    <span style="font-weight: 700; color: var(--theme-primary);">${value}</span>
  </div>
  <div class="metric-trend-bar" style="height: 4px; background: rgba(0,0,0,0.05); border-radius: 2px; overflow: hidden;">
    <span style="display: block; height: 100%; width: ${progress}; background: var(--theme-primary);"></span>
  </div>
</div>`;
  }

  /**
   * 构建进度环
   */
  buildProgressRing(component, options) {
    const { value = 68 } = options;
    return `<div style="display: flex; flex-direction: column; align-items: center; gap: 12px;">
  <div class="progress-ring" style="--progress-value: ${value}; width: 80px; height: 80px; border-radius: 50%; background: conic-gradient(var(--theme-primary) ${value * 3.6}deg, rgba(0,0,0,0.05) 0deg); display: flex; align-items: center; justify-content: center; position: relative;">
    <div style="width: 60px; height: 60px; background: var(--bg-card); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700;">${value}%</div>
  </div>
  <span style="font-size: 12px; color: var(--text-secondary);">运行负载</span>
</div>`;
  }

  /**
   * 构建时间轴条
   */
  buildTimelineStrip(component, options) {
    const { label = '当前进度', progress = '60%' } = options;
    return `<div class="timeline-strip" style="background: var(--bg-card); padding: 12px; border-radius: 8px; border: 1px solid var(--glass-border-light);">
  <div class="timeline-strip-item">
    <div class="timeline-strip-time" style="font-size: 12px; color: var(--text-tertiary); margin-bottom: 4px;">${label}</div>
    <div class="timeline-strip-bar" style="height: 6px; background: rgba(0,0,0,0.05); border-radius: 3px; overflow: hidden;">
      <span style="display: block; height: 100%; width: ${progress}; background: var(--theme-primary);"></span>
    </div>
  </div>
</div>`;
  }
}




// 导出供使用
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ComponentGenerator;
}
