# A股市场分析工具

这是一个综合性的A股市场分析工具集，提供市场情绪分析、板块热度监控以及个股技术分析功能，帮助投资者全方位了解市场状态和把握交易机会。

## 功能特点

### 市场宏观分析
- **市场概况分析**：包括上涨/下跌家数、涨跌比、总成交额和平均涨跌幅等指标
- **板块热度分析**：识别当前热门板块和潜力板块
- **市场情绪评分**：生成0-100分的市场情绪得分，并给出相应投资建议
- **数据报告生成**：自动保存分析报告为CSV格式

### 个股技术分析
- **分时数据分析**：获取和分析股票分时交易数据
- **交易信号识别**：基于多指标分析识别买入卖出信号
- **支撑压力位预测**：预测可能的买卖点位和反弹/回调幅度
- **技术指标分析**：集成MACD、均线、成交量等多维度技术指标

## 主要组件

### 市场分析模块
- `MarketSentiment` 类：市场情绪分析引擎，提供市场整体状态和板块分析功能
- 数据缓存机制：减少重复API调用，提高响应速度

### 个股分析模块
- `minute.py`：分时数据分析工具，包含以下功能：
  - 获取股票分时交易数据
  - 基于趋势分析的交易信号识别
  - 支持MACD、均线、成交量等多维度技术分析
  - 预测未来可能的支撑位和压力位

## 技术依赖

- Python 3.x
- 第三方库：
  - akshare：A股数据获取
  - pandas：数据处理
  - numpy：数值计算

## 使用方法

### 市场情绪分析
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

### 分时数据分析
```python
from py.minute import analyze_trading_signals, predict_price_points

# 分析股票交易信号
stock_code = "sh600519"  # 贵州茅台
signals = analyze_trading_signals(stock_code)

# 预测支撑压力位
predictions = predict_price_points(stock_code)
```

## 输出示例

### 市场分析输出
- 市场概况（涨跌家数、成交额等）
- 热门板块排名
- 潜力板块排名
- 市场情绪评分（0-100分）
- 投资建议（1-5星级）

市场分析报告将自动保存为CSV文件。

### 个股分析输出
- 交易信号（买入/卖出点位及强度）
- 支撑位和压力位预测
- 各预测点位的置信度和原因
- 预期反弹/回调幅度

## 注意事项

- 该工具依赖网络连接获取实时市场数据
- 分析结果仅供参考，投资决策请结合其他因素综合考虑