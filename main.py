import os
import discord
import openai
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# 載入 API 金鑰
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# 設定 Discord bot
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'✅ Bot 上線！{client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith("!股票超人 "):
        stock_code = message.content.split(" ")[1]
        yf_code = f"{stock_code}.TW"

        try:
            # 抓上半年資料
            today = datetime.today()
            start_date = today.replace(month=1, day=1)
            stock = yf.Ticker(yf_code)
            hist = stock.history(start=start_date.strftime('%Y-%m-%d'), end=today.strftime('%Y-%m-%d'))

            if hist.empty:
                await message.channel.send("❌ 找不到資料")
                return

            info = stock.info
            name = info.get("longName", "未知公司")
            latest = hist.iloc[-1]
            prev_close = hist.iloc[-2]["Close"]
            change = latest["Close"] - prev_close
            change_pct = (change / prev_close) * 100

            # 繪圖
            plt.figure(figsize=(16, 6))
            plt.plot(hist.index, hist["Close"], marker='o')
            plt.title(f"{name}（{stock_code}）2025 上半年走勢", fontsize=16)
            plt.xlabel("日期")
            plt.ylabel("收盤價（元）")
            plt.grid(True)
            plt.xticks(rotation=45)
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            plt.tight_layout()
            chart_path = "chart.png"
            plt.savefig(chart_path)
            plt.close()

            # GPT 分析
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": f"請幫我分析 {name}（{stock_code}）2025 上半年股價走勢，列出趨勢、支撐阻力與投資建議"}]
            )
            analysis = response.choices[0].message.content.strip()

            # 回傳 Discord
            reply = (
                f"📈 {name} ({stock_code})\n"
                f"開盤：{latest['Open']:.2f} 元\n"
                f"收盤：{latest['Close']:.2f} 元\n"
                f"最高：{latest['High']:.2f} 元\n"
                f"最低：{latest['Low']:.2f} 元\n"
                f"漲跌：{change:+.2f} 元（{change_pct:+.2f}%）\n\n"
                f"💬 GPT 分析：\n{analysis}"
            )
            await message.channel.send(reply)
            await message.channel.send(file=discord.File(chart_path))

        except Exception as e:
            await message.channel.send(f"⚠️ 錯誤：{e}")

client.run(DISCORD_TOKEN)
