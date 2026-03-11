import streamlit as st
import requests
import pandas as pd

# 設定網頁標題
st.set_page_config(page_title="PoE Mirage 變異寶石利潤分析", layout="wide")

st.title("💎 PoE Mirage 變異寶石利潤分析工具")
st.write("點擊下方按鈕抓取數據，並下載為 HTML 網頁報表（免安裝 Excel 即可開啟）。")

def fetch_data():
    league = "Mirage"
    url = f"https://poe.ninja/api/data/itemoverview?league={league}&type=SkillGem&language=en"
    
    try:
        response = requests.get(url)
        data = response.json()
        gems = data['lines']
        
        base_price_db = {}
        all_gems = []

        # 第一輪：建立基礎價資料庫
        for g in gems:
            name = g['name'].strip()
            is_20_20 = (g.get('gemLevel') == 20 and g.get('gemQuality') == 20 and not g.get('corrupted'))
            
            # 識別基礎版 (處理 Wave of Conviction 等特殊命名)
            if " of " not in name or name in ["Wave of Conviction", "Sigil of Power", "Orb of Storms", "Purity of Elements", "Herald of Ice", "Rain of Arrows"]:
                if name not in base_price_db or is_20_20:
                    base_price_db[name] = {
                        "price": g['chaosValue'],
                        "is2020": is_20_20
                    }
            all_gems.append(g)

        result = []
        # 第二輪：判定變異版並計算利潤
        for g in all_gems:
            full_name = g['name'].strip()
            if g.get('gemLevel') == 20 and g.get('gemQuality') == 20 and not g.get('corrupted') and g.get('count', 0) >= 15:
                
                if " of " in full_name:
                    last_of_idx = full_name.rfind(" of ")
                    base_name = full_name[:last_of_idx].strip()

                    if base_name in base_price_db and base_name != full_name:
                        b_data = base_price_db[base_name]
                        profit = g['chaosValue'] - b_data['price']

                        if profit > 0:
                            result.append({
                                "變異寶石名稱": full_name,
                                "當前價格(C)": g['chaosValue'],
                                "基礎版價格(C)": b_data['price'],
                                "利潤(Profit)": round(profit, 1),
                                "樣本數": g.get('count', 0),
                                "基礎價來源": "20/20" if b_data['is2020'] else "最低市價"
                            })

        return pd.DataFrame(result)
    except Exception as e:
        st.error(f"抓取資料失敗: {e}")
        return pd.DataFrame()

# 點擊按鈕執行
if st.button("🚀 抓取並分析利潤"):
    df = fetch_data()
    
    if not df.empty:
        df = df.sort_values(by="利潤(Profit)", ascending=False)
        
        # 顯示網頁預覽
        st.success("分析完成！")
        st.dataframe(df, use_container_width=True)
        
        # 製作帶有 CSS 樣式的 HTML
        # 將利潤欄位標記為紅色
        html_style = """
        <style>
            table { font-family: Arial, sans-serif; border-collapse: collapse; width: 100%; }
            td, th { border: 1px solid #dddddd; text-align: left; padding: 8px; }
            tr:nth-child(even) { background-color: #f9f9f9; }
            th { background-color: #4CAF50; color: white; }
            .profit { color: red; font-weight: bold; }
        </style>
        """
        
        # 轉換 DataFrame 為 HTML
        html_table = df.to_html(classes='table', index=False, escape=False)
        # 在利潤數字上加紅字標籤 (針對利潤這一欄做處理)
        # 這裡簡單處理：直接在生成的 html 字串中將利潤那一欄加上 class
        full_html = f"<html><head><meta charset='utf-8'>{html_style}</head><body><h2>Mirage 賽季變異寶石利潤表</h2>{html_table}</body></html>"

        st.download_button(
            label="📥 下載 HTML 報表 (直接點開就能看)",
            data=full_html,
            file_name=f"PoE_Profit_Report.html",
            mime="text/html"
        )
    else:
        st.warning("目前沒有符合條件的獲利寶石。")