import akshare as ak
import pandas as pd

def get_stock_intraday_data(stock_code):
    """获取股票分时数据"""
    try:
        # 获取分时数据
        stock_zh_a_minute = ak.stock_zh_a_minute(
            symbol=stock_code, 
            period='1',  # 1分钟
            adjust=""
        )
        return stock_zh_a_minute
    except Exception as e:
        print(f"获取分时数据失败: {e}")
        return None

def analyze_trading_signals(stock_code):
    """
    分析分时数据并给出交易信号
    基于趋势分析的交易信号识别系统
    """
    try:
        # 获取分时数据
        df = get_stock_intraday_data(stock_code)
        if df is None or df.empty:
            return None

        # 转换数据类型
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce')

        # 计算技术指标
        df['ma10'] = df['close'].rolling(window=10).mean()  # 10分钟均线，若窗口大小的数据不足，返回值为NaN
        df['ma30'] = df['close'].rolling(window=30).mean()  # 30分钟均线
        df['volume_ma10'] = df['volume'].rolling(window=10).mean()

        # 计算MACD
        exp12 = df['close'].ewm(span=12, adjust=False).mean() # 12周期EMA（快速线）
        exp26 = df['close'].ewm(span=26, adjust=False).mean() # 26周期EMA（慢速线）
        df['MACD'] = exp12 - exp26 # 当 MACD 为正值时，短期趋势向上；负值则表示短期趋势向下。
        df['SIGNAL'] = df['MACD'].ewm(span=9, adjust=False).mean() # 用于平滑 MACD 线的波动，减少假信号
        df['HIST'] = df['MACD'] - df['SIGNAL']

        # 计算动量指标
        df['momentum'] = df['close'].diff(periods=5)
        df['volume_change'] = df['volume'].pct_change()

        # 初始化信号列表
        signals = []

        # 遍历数据（从第31行开始，因为需要30分钟移动平均）
        for i in range(30, len(df)):
            current_price = df['close'].iloc[i]
            current_volume = df['volume'].iloc[i]
            timestamp = df.index[i]

            # 趋势判断
            ma10_trend = df['ma10'].iloc[i] - df['ma10'].iloc[i-1]
            ma30_trend = df['ma30'].iloc[i] - df['ma30'].iloc[i-1]
            macd_hist = df['HIST'].iloc[i]
            momentum = df['momentum'].iloc[i]
            volume_change = df['volume_change'].iloc[i]

            # 买点信号
            if (ma10_trend > 0 and  # 短期趋势向上
                df['ma10'].iloc[i] > df['ma30'].iloc[i] and  # 短期均线在长期均线上方
                df['ma10'].iloc[i-1] <= df['ma30'].iloc[i-1] and  # 发生金叉
                macd_hist > 0 and  # MACD柱状图为正
                current_volume > df['volume_ma10'].iloc[i] * 1.2):  # 放量确认
                signals.append({
                    'time': timestamp,
                    'price': current_price,
                    'signal': '买入',
                    'reason': '趋势突破买点',
                    'strength': '强'
                })

            # 回调买点
            elif (ma10_trend > 0 and  # 短期趋势仍向上
                  df['ma10'].iloc[i] > df['ma30'].iloc[i] and  # 均线维持多头排列
                  current_price < df['ma10'].iloc[i] and  # 价格回调到均线附近
                  momentum > 0 and  # 动量转正
                  volume_change > 0):  # 量能开始放大
                signals.append({
                    'time': timestamp,
                    'price': current_price,
                    'signal': '买入',
                    'reason': '回调企稳买点',
                    'strength': '中'
                })

            # 卖点信号
            elif (ma10_trend < 0 and  # 短期趋势向下
                  df['ma10'].iloc[i] < df['ma30'].iloc[i] and  # 短期均线在长期均线下方
                  df['ma10'].iloc[i-1] >= df['ma30'].iloc[i-1] and  # 发生死叉
                  macd_hist < 0):  # MACD柱状图为负
                signals.append({
                    'time': timestamp,
                    'price': current_price,
                    'signal': '卖出',
                    'reason': '趋势转折卖点',
                    'strength': '强'
                })

            # 获利了结卖点
            elif (ma10_trend > 0 and  # 虽然趋势向上
                  momentum < 0 and  # 但动量减弱
                  current_volume < df['volume_ma10'].iloc[i] * 0.8 and  # 量能萎缩
                  current_price > df['ma10'].iloc[i] * 1.03):  # 价格明显偏离均线
                signals.append({
                    'time': timestamp,
                    'price': current_price,
                    'signal': '卖出',
                    'reason': '强势获利卖点',
                    'strength': '中'
                })

        signals_df = pd.DataFrame(signals)
        if not signals_df.empty:
            signals_df['price_change'] = signals_df['price'].pct_change()
            signals_df = signals_df.round(6)  # 四舍五入到3位小数

        return signals_df

    except Exception as e:
        print(f"分析交易信号时出错: {e}")
        return None

# 预测未来可能的买卖点位 价格预测模块
def predict_price_points(stock_code):
    """
    预测未来可能的买卖点位
    """
    try:
        df = get_stock_intraday_data(stock_code)
        if df is None or df.empty:
            return None

        # 数据预处理
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce')

        # 计算基础指标
        df['ma10'] = df['close'].rolling(window=10).mean()
        df['ma30'] = df['close'].rolling(window=30).mean()
        df['std20'] = df['close'].rolling(window=20).std()  # 20周期标准差

        # MACD指标
        exp12 = df['close'].ewm(span=12, adjust=False).mean()
        exp26 = df['close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp12 - exp26
        df['SIGNAL'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['HIST'] = df['MACD'] - df['SIGNAL']

        # 计算支撑压力位
        latest_price = df['close'].iloc[-1]
        high_prices = df['close'].nlargest(5)  # 最近高点
        low_prices = df['close'].nsmallest(5)  # 最近低点

        # 计算趋势强度
        price_change = df['close'].pct_change()
        trend_strength = price_change.rolling(window=20).mean() / price_change.rolling(window=20).std()
        current_trend = trend_strength.iloc[-1]

        # 计算波动范围
        volatility = df['std20'].iloc[-1] / df['close'].iloc[-1]

        # 预测结果
        result = {
            'current_price': latest_price,
            'predictions': []
        }

        # 支撑位预测（买点）
        support_levels = []
        for ma in [df['ma10'].iloc[-1], df['ma30'].iloc[-1]]:
            if ma < latest_price:
                support_levels.append(ma)
        support_levels.extend(low_prices[low_prices < latest_price])

        # 压力位预测（卖点）
        resistance_levels = []
        for ma in [df['ma10'].iloc[-1], df['ma30'].iloc[-1]]:
            if ma > latest_price:
                resistance_levels.append(ma)
        resistance_levels.extend(high_prices[high_prices > latest_price])

        # 生成买点预测
        for support in sorted(set(support_levels))[:3]:  # 取最近的3个支撑位
            confidence = min(0.9, max(0.3, 1 - abs(support - latest_price) / latest_price))
            reason = []

            if abs(support - df['ma10'].iloc[-1]) / latest_price < 0.01:
                reason.append("接近10分钟均线支撑")
                confidence += 0.1
            if abs(support - df['ma30'].iloc[-1]) / latest_price < 0.01:
                reason.append("接近30分钟均线支撑")
                confidence += 0.15
            if df['HIST'].iloc[-1] > 0:
                reason.append("MACD指标趋势向好")
                confidence += 0.1

            result['predictions'].append({
                'type': '买入',
                'price': round(support, 2),
                'confidence': round(min(0.95, confidence), 2),
                'reasons': reason or ["价格接近历史支撑位"],
                'expected_bounce': f"{round(volatility * 100 * 2, 1)}%"
            })
 
        # 生成卖点预测    
        for resistance in sorted(set(resistance_levels))[:3]:  # 取最近的3个压力位
            confidence = min(0.9, max(0.3, 1 - abs(resistance - latest_price) / latest_price))
            reason = []

            if abs(resistance - df['ma10'].iloc[-1]) / latest_price < 0.01:
                reason.append("接近10分钟均线压力")
                confidence += 0.1
            if abs(resistance - df['ma30'].iloc[-1]) / latest_price < 0.01:
                reason.append("接近30分钟均线压力")
                confidence += 0.15
            if df['HIST'].iloc[-1] < 0:
                reason.append("MACD指标趋势转弱")
                confidence += 0.1

            result['predictions'].append({
                'type': '卖出',
                'price': round(resistance, 2),
                'confidence': round(min(0.95, confidence), 2),
                'reasons': reason or ["价格接近历史压力位"],
                'expected_drop': f"{round(volatility * 100 * 2, 1)}%"
            })

        # 按信心度排序
        result['predictions'] = sorted(result['predictions'], key=lambda x: x['confidence'], reverse=True)

        return result

    except Exception as e:
        print(f"预测价格点位时出错: {e}")
        return None
    
def check_Stock(test_stock):
    # 测试交易信号
    print("=== 测试交易信号 ===")
    signals = analyze_trading_signals(test_stock)
    if signals is not None and not signals.empty:
        print("\n交易信号:")
        print(signals.tail())

    # 测试价格预测
    print("\n=== 测试价格预测 ===")
    predictions = predict_price_points(test_stock)
    if predictions:
        print(f"\n当前价格: {predictions['current_price']:.2f}")
        print("\n预测的买卖点:")
        for pred in predictions['predictions']:
            print(f"\n{pred['type']}点位: {pred['price']}")
            print(f"置信度: {pred['confidence']*100:.1f}%")
            print(f"原因: {', '.join(pred['reasons'])}")
            if pred['type'] == '买入':
                print(f"预期反弹幅度: {pred['expected_bounce']}")
            else:
                print(f"预期回调幅度: {pred['expected_drop']}")

if __name__ == "__main__":
    # 测试股票代码
    test_stock = "sh600519"  # 贵州茅台
    check_Stock(test_stock)

