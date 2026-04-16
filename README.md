# API 性能基准测试与监控

这个仓库是一个自动化的监控系统，用于对比官方 OpenAI API 和我们的中转 (Proxy) 接口在 GitHub 环境中的表现。

## 📊 测试指标
- **首字延迟 (TTFB)**: 用户感知响应快慢的关键（流式）。
- **总耗时 (Total)**: 完整响应的时间。
- **200字样文**: 用于直观对比内容的一致性。

## 🔗 数据访问
测试结果每小时更新一次，您可以在以下位置获取：
- **Markdown 报告**: 见底部的测试表格。
- **JSON 数据**: [api_stats.json](./api_stats.json) (可供前端展示使用)。

## 🚀 部署指南
1. 在仓库的 **Settings > Secrets and variables > Actions** 中添加以下密钥：
   - `OFFICIAL_KEY`: 官方 OpenAI 的 API Key。
   - `PROXY_KEY`: 中转接口的 API Key。
2. 运行 GitHub Action 或等待定时触发。

---

## 📈 最新测试结果
*数据将通过 GitHub Actions 自动更新...*

| 接口类型 | 平均首字延迟 (ms) | 平均总耗时 (ms) | 状态 |
| :--- | :--- | :--- | :--- |
| 官方 (Direct) | - | - | 等待第一次运行 |
| 中转 (Proxy) | - | - | 等待第一次运行 |
