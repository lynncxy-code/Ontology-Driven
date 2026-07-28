# Lingjing Core Components

> 灵境核心组件样式库（可选）

## 说明

此目录包含可选的组件样式实现。主要设计令牌和规范请参考:

- **[设计令牌索引](../docs/design/TOKEN_INDEX.md)** - 完整的设计令牌
- **[组件API文档](../docs/components/COMPONENT_API.md)** - 组件定义
- **[组件清单](../data/components.csv)** - 组件列表

## 结构

```
components/
├── README.md           # 本文件
└── src/
    └── styles/         # 样式文件（CSS/SCSS）
```

## 使用方法

组件样式基于灵境设计令牌构建，可以直接集成到项目中，或作为参考实现。

### 集成方式

1. **直接引用**: 将样式文件导入到项目中
2. **参考实现**: 根据设计令牌自行实现
3. **组件库**: 配合 React/Vue 等框架使用

### 关键规范

- 使用 CSS 变量访问设计令牌
- 遵循玻璃拟态和呼吸动效原则
- 严格避免反模式（扫描线、噪点纹理、刚性边框）

## 相关资源

- [设计令牌](../data/design-tokens.csv)
- [反模式清单](../data/anti-patterns.csv)
- [快速参考](../docs/QUICK_REFERENCE.md)
