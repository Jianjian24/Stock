import akshare as ak
import pandas as pd
import numpy as np
import os
import time
from datetime import datetime, timedelta

class MarketSentiment:
    def __init__(self):
        self.sentiment_score = 0
        self.hot_sectors = []
        self.potential_sectors = []
        self.market_status = ""
        self.dfMarket = None

    def get_market_overview(self):
        try:
            # 获取A股市场实时行情
            def get_market_data():
                # 简化版：获取最近的工作日
                def get_latest_workday():
                    today = datetime.now()
                    # 如果今天是工作日且在交易时间内，使用今天
                    if today.weekday() < 5:  # 周一到周五
                        return today.strftime("%Y%m%d")
                    
                    # 否则找最近的周五
                    days_back = today.weekday() - 4  # 距离周五的天数
                    if days_back < 0:
                        days_back += 7
                    workday = today - timedelta(days=days_back)
                    return workday.strftime("%Y%m%d")
                
                latest_workday = get_latest_workday()
                cache_file = "market_report_{}.csv".format(latest_workday)
                
                if os.path.exists(cache_file):
                    # 检查文件修改时间，如果在1分钟内，直接使用缓存
                    file_mtime = os.path.getmtime(cache_file)
                    if time.time() - file_mtime < 60:  # 60秒内的缓存有效
                        return pd.read_csv(cache_file)

                # 获取新数据并缓存
                df = ak.stock_zh_a_spot()
                df.to_csv(cache_file, index=False)
                self.dfMarket = df
                return df


            df_market = get_market_data()

            if df_market is None or df_market.empty:
                raise ValueError("未获取到市场数据")

            # 计算涨跌家数
            up_count = len(df_market[df_market['涨跌幅'] > 0])
            down_count = len(df_market[df_market['涨跌幅'] < 0])
            up_down_ratio = up_count / (down_count if down_count > 0 else 1)

            # 计算总成交额和平均涨跌幅
            total_amount = df_market['成交额'].sum() / 100000000  # 转化为亿元
            avg_change = df_market['涨跌幅'].mean()

            return {
                'up_count': up_count,
                'down_count': down_count,
                'up_down_ratio': up_down_ratio,
                'total_amount': total_amount,
                'avg_change': avg_change
            }
        except Exception as e:
            print(f"获取市场概况失败: {e}")
            return {
                'up_count': 0,
                'down_count': 0,
                'up_down_ratio': 1,
                'total_amount': 0,
                'avg_change': 0
            }

    def get_sector_analysis(self):
        """获取板块分析"""
        try:
            df_sectors = None
            error_msg = ""

            # 尝试获取行业板块数据
            try:
                df_sectors = ak.stock_board_industry_name_em()
                if not df_sectors.empty:
                    # 标准化列名
                    df_sectors.columns = [str(col).strip() for col in df_sectors.columns]
                    column_mapping = {
                        '行业': '板块名称',
                        '名称': '板块名称',
                        '涨跌额': '变动金额',  # 使用涨跌额替代成交额
                        '涨跌幅': '涨跌幅',
                        '涨跌幅(%)': '涨跌幅'
                    }
                    df_sectors = df_sectors.rename(columns=column_mapping)

            except Exception as e:
                error_msg = f"行业板块接口失败: {str(e)}"
                print(error_msg)
                return {
                    'hot_sectors': pd.DataFrame(columns=['板块名称', '涨跌幅', '变动金额']),
                    'potential_sectors': pd.DataFrame(columns=['板块名称', '涨跌幅', '变动金额'])
                }

            if df_sectors is None or df_sectors.empty:
                raise ValueError(f"获取板块数据失败: {error_msg}")

            # 确保必要列存在
            required_columns = ['板块名称', '涨跌幅', '变动金额']
            for col in required_columns:
                if col not in df_sectors.columns:
                    raise ValueError(f"数据缺少必要列：{col}")

            # 数据清理和转换
            # 处理涨跌幅数据
            df_sectors['涨跌幅'] = pd.to_numeric(
                df_sectors['涨跌幅'].astype(str).str.replace('%', '').str.replace('+', ''), 
                errors='coerce'
            )

            # 处理涨跌额数据
            df_sectors['变动金额'] = pd.to_numeric(
                df_sectors['变动金额'].astype(str).str.replace(',', ''), 
                errors='coerce'
            )

            # 清理数据
            df_sectors = df_sectors.fillna(0)
            df_sectors['涨跌幅'] = df_sectors['涨跌幅'].astype(float)
            df_sectors['变动金额'] = df_sectors['变动金额'].astype(float)

            # 获取前5个涨幅最大的板块
            hot_sectors = df_sectors.sort_values('涨跌幅', ascending=False).head(10)

            # 获取资金流入且涨幅较小的潜力板块
            # 计算综合得分：资金流入量为主要考虑因素，涨幅接近0为次要考虑因素
            df_sectors['potential_score'] = df_sectors['变动金额'] - abs(df_sectors['涨跌幅']) * 100
            # 只考虑资金净流入的板块
            potential_sectors = df_sectors[df_sectors['变动金额'] > 0].sort_values(by='potential_score', ascending=False).head(10)

            # 确保返回的DataFrame包含所需的所有列
            result_columns = ['板块名称', '涨跌幅', '变动金额']
            hot_sectors = hot_sectors.reindex(columns=result_columns)
            potential_sectors = potential_sectors.reindex(columns=result_columns)

            return {
                'hot_sectors': hot_sectors,
                'potential_sectors': potential_sectors
            }
        except Exception as e:
            print(f"获取板块分析失败: {e}")
            empty_df = pd.DataFrame(columns=['板块名称', '涨跌幅', '变动金额'])
            return {
                'hot_sectors': empty_df,
                'potential_sectors': empty_df
            }

    def get_market_sentiment(self):
        """
        计算市场情绪分数
        返回值范围：0到100，数值越大表示市场情绪越乐观
        0-20: 极度悲观
        20-40: 偏悲观
        40-60: 中性
        60-80: 偏乐观
        80-100: 极度乐观
        """
        try:
            # 获取大盘指数数据
            df_index = ak.stock_zh_index_daily_em(symbol="sh000001")  # 获取上证指数
            if df_index is None or df_index.empty:
                raise ValueError("未获取到指数数据")

            # 计算最近的涨跌幅
            latest_day = df_index.iloc[-1]
            prev_day = df_index.iloc[-2]

            # 1. 计算涨跌幅得分 (权重40%)
            change_pct = (latest_day['close'] - prev_day['close']) / prev_day['close'] * 100
            # 将涨跌幅从-10%~10%映射到0-40分
            change_score = min(max((change_pct + 10) * 2, 0), 40)

            # 2. 计算成交量变化得分 (权重30%)
            volume_ratio = latest_day['volume'] / prev_day['volume']
            # 将成交量比从0.5~1.5映射到0-30分
            volume_score = min(max((volume_ratio - 0.5) * 30, 0), 30)

            # 3. 计算涨跌家数比例得分 (权重30%)
            try:
                up_count = len(self.dfMarket[self.dfMarket['涨跌幅'] > 0])
                down_count = len(self.dfMarket[self.dfMarket['涨跌幅'] < 0])
                total = up_count + down_count
                if total > 0:
                    # 将涨跌比从0~1映射到0-30分
                    advance_decline_ratio = up_count / total
                    breadth_score = min(max(advance_decline_ratio * 30, 0), 30)
                else:
                    breadth_score = 0

            except:
                breadth_score = 0

            # 综合计算最终情绪分数
            final_score = change_score + volume_score + breadth_score

            # 输出调试信息
            print(f"[市场情绪] 涨跌得分: {change_score:.1f}, 成交量得分: {volume_score:.1f}, 市场宽度得分: {breadth_score:.1f}")
            print(f"[市场情绪] 最终得分: {final_score:.1f}/100")

            return float(final_score)

        except Exception as e:
            print(f"[错误] 计算市场情绪失败: {e}")
            return 50.0  # 出错时返回中性值

    def calculate_sentiment_score(self, market_data, sector_data):
        """计算市场情绪得分"""
        if not market_data or not sector_data:
            return 0

        score = 0

        # 基于涨跌比例计算分数（权重：40%）
        up_down_score = min(100, market_data['up_down_ratio'] * 50)
        score += up_down_score * 0.4

        # 基于平均涨跌幅计算分数（权重：30%）
        change_score = (market_data['avg_change'] + 10) * 5  # 转换到0-100区间
        change_score = max(0, min(100, change_score))
        score += change_score * 0.3

        # 基于成交额计算分数（权重：30%）
        amount_score = min(100, market_data['total_amount'] / 100 * 10)
        score += amount_score * 0.3

        return round(score, 2)

    def get_investment_suggestion(self, sentiment_score):
        """根据情绪得分给出投资建议"""
        if sentiment_score >= 80:
            return "5星 - 市场情绪极度乐观，注意防范风险"
        elif sentiment_score >= 60:
            return "4星 - 市场情绪偏乐观，可适度参与"
        elif sentiment_score >= 40:
            return "3星 - 市场情绪中性，保持观望"
        elif sentiment_score >= 20:
            return "2星 - 市场情绪偏悲观，谨慎参与"
        else:
            return "1星 - 市场情绪低迷，建议观望"

    def analyze_market(self):
        """分析市场状况并输出结果"""
        try:
            print("\n=== 市场情绪分析报告 ===")
            print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            # 1. 获取市场数据
            market_data = self.get_market_overview()
            print("\n市场概况:")
            print(f"上涨家数: {market_data['up_count']}")
            print(f"下跌家数: {market_data['down_count']}")
            print(f"涨跌比: {market_data['up_down_ratio']:.2f}")
            print(f"总成交额: {market_data['total_amount']:.2f}亿")
            print(f"平均涨跌幅: {market_data['avg_change']:.2f}%")

            # 2. 获取板块分析
            sector_data = self.get_sector_analysis()
            if not sector_data['hot_sectors'].empty:
                print("\n热门板块:")
                hot_sectors_display = sector_data['hot_sectors'][['板块名称', '涨跌幅', '变动金额']]
                hot_sectors_display['涨跌幅'] = hot_sectors_display['涨跌幅'].apply(lambda x: f"{x:.2f}%")
                hot_sectors_display['变动金额'] = hot_sectors_display['变动金额'].apply(lambda x: f"{x:.2f}")
                print(hot_sectors_display.to_string(index=False))

                print("\n潜力板块:")
                potential_sectors_display = sector_data['potential_sectors'][['板块名称', '涨跌幅', '变动金额']]
                potential_sectors_display['涨跌幅'] = potential_sectors_display['涨跌幅'].apply(lambda x: f"{x:.2f}%")
                potential_sectors_display['变动金额'] = potential_sectors_display['变动金额'].apply(lambda x: f"{x:.2f}")
                print(potential_sectors_display.to_string(index=False))

            # 4. 计算市场情绪
            sentiment_score = self.get_market_sentiment()
            print(f"\n市场情绪得分: {sentiment_score:.2f}/100")

            # 5. 生成投资建议
            suggestion = self.get_investment_suggestion(sentiment_score)
            print(f"投资建议: {suggestion}")

            # 6. 保存分析报告
            report_saved = self.save_report(market_data, sector_data, sentiment_score, suggestion)
            print(f"\n分析报告已保存至: {report_saved}")

        except Exception as e:
            print(f"市场分析执行出现错误: {e}")
            print("请检查网络连接并重试，或查看详细错误信息")

    def save_report(self, market_data, sector_data, sentiment_score, suggestion):
        """保存分析报告到CSV文件"""
        try:
            report_data = {
            '分析时间': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            '上涨家数': [market_data['up_count']],
            '下跌家数': [market_data['down_count']],
            '涨跌比': [round(market_data['up_down_ratio'], 2)],
            '总成交额(亿)': [round(market_data['total_amount'], 2)],
            '平均涨跌幅(%)': [round(market_data['avg_change'], 2)],
            '市场情绪得分': [sentiment_score],
            '投资建议': [suggestion],
            '热门板块TOP1': [sector_data['hot_sectors'].iloc[0]['板块名称'] if not sector_data['hot_sectors'].empty else ''],
            '热门板块TOP2': [sector_data['hot_sectors'].iloc[1]['板块名称'] if len(sector_data['hot_sectors']) > 1 else ''],
            '热门板块TOP3': [sector_data['hot_sectors'].iloc[2]['板块名称'] if len(sector_data['hot_sectors']) > 2 else '']
        }

            df_report = pd.DataFrame(report_data)
            filename = f"market_report_final{datetime.now().strftime('%Y%m%d')}.csv"
            df_report.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"\n分析报告已保存至: {filename}")

        except Exception as e:
            print(f"保存报告时出现错误: {e}")

if __name__ == "__main__":
    analyzer = MarketSentiment()
    analyzer.analyze_market()
    # analyzer.get_market_sentiment()
    # analyzer.get_sector_analysis()