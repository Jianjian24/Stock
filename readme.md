# 股票市场情绪分析工具

这是一个用于分析A股市场情绪和板块热度的工具，帮助投资者了解市场整体状态和潜在投资机会。

## 功能特点

- **市场概况分析**：包括上涨/下跌家数、涨跌比、总成交额和平均涨跌幅等指标
- **板块热度分析**：识别当前热门板块和潜力板块
- **市场情绪评分**：生成0-100分的市场情绪得分，并给出相应投资建议
- **数据报告生成**：自动保存分析报告为CSV格式

## 主要组件

- `MarketSentiment` 类：核心分析引擎，提供市场情绪和板块分析功能
- 数据缓存机制：减少重复API调用，提高响应速度

## 技术依赖

- Python 3.x
- 第三方库：
  - akshare：A股数据获取
  - pandas：数据处理
  - numpy：数值计算

## 使用方法

```python
from py.trade_sentiment import MarketSentiment

# 创建分析器实例
analyzer = MarketSentiment()

# 执行完整分析
analyzer.analyze_market()

# 或者单独调用特定功能
sentiment_score = analyzer.get_market_sentiment()
sector_data = analyzer.get_sector_analysis()
```

## 输出示例

分析结果将显示：
- 市场概况（涨跌家数、成交额等）
- 热门板块排名
- 潜力板块排名
- 市场情绪评分（0-100分）
- 投资建议（1-5星级）

分析报告将自动保存为CSV文件。

## 注意事项

- 该工具依赖网络连接获取实时市场数据
- 分析结果仅供参考，投资决策请结合其他因素综合考虑
