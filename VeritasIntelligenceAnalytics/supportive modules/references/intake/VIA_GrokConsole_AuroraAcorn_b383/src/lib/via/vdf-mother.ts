/** Compact mother VDF SSOT: TW focus universe + ENG047 + unified params. */
export const VDF_MOTHER_SCHEMA = "VIA.VDF.MotherCompact.v1";
export const TW_UNIVERSE_COUNTS = { groups: 31, members: 149, leaders: 41, twse: 119, tpex: 30 } as const;
export type TwMember = { ticker: string; name: string; market: "TWSE" | "TPEX"; yfinance: string; bloomberg: string; group: string; role: string };
export const TW_UNIVERSE: TwMember[] = [
  {
    "ticker": "2330",
    "name": "台積電",
    "market": "TWSE",
    "yfinance": "2330.TW",
    "bloomberg": "2330 TT",
    "group": "半導體",
    "role": "LEADER"
  },
  {
    "ticker": "2454",
    "name": "聯發科",
    "market": "TWSE",
    "yfinance": "2454.TW",
    "bloomberg": "2454 TT",
    "group": "半導體",
    "role": "PEER"
  },
  {
    "ticker": "2303",
    "name": "聯電",
    "market": "TWSE",
    "yfinance": "2303.TW",
    "bloomberg": "2303 TT",
    "group": "半導體",
    "role": "PEER"
  },
  {
    "ticker": "5347",
    "name": "世界先進",
    "market": "TPEX",
    "yfinance": "5347.TWO",
    "bloomberg": "5347 TT",
    "group": "半導體",
    "role": "LAGGARD"
  },
  {
    "ticker": "6770",
    "name": "力積電",
    "market": "TWSE",
    "yfinance": "6770.TW",
    "bloomberg": "6770 TT",
    "group": "半導體",
    "role": "LAGGARD"
  },
  {
    "ticker": "3711",
    "name": "日月光投控",
    "market": "TWSE",
    "yfinance": "3711.TW",
    "bloomberg": "3711 TT",
    "group": "半導體",
    "role": "LEADER"
  },
  {
    "ticker": "6488",
    "name": "環球晶",
    "market": "TPEX",
    "yfinance": "6488.TWO",
    "bloomberg": "6488 TT",
    "group": "半導體",
    "role": "PEER"
  },
  {
    "ticker": "2317",
    "name": "鴻海",
    "market": "TWSE",
    "yfinance": "2317.TW",
    "bloomberg": "2317 TT",
    "group": "AI 伺服器",
    "role": "LEADER"
  },
  {
    "ticker": "2382",
    "name": "廣達",
    "market": "TWSE",
    "yfinance": "2382.TW",
    "bloomberg": "2382 TT",
    "group": "AI 伺服器",
    "role": "PEER"
  },
  {
    "ticker": "3231",
    "name": "緯創",
    "market": "TWSE",
    "yfinance": "3231.TW",
    "bloomberg": "3231 TT",
    "group": "AI 伺服器",
    "role": "PEER"
  },
  {
    "ticker": "6669",
    "name": "緯穎",
    "market": "TWSE",
    "yfinance": "6669.TW",
    "bloomberg": "6669 TT",
    "group": "AI 伺服器",
    "role": "LEADER"
  },
  {
    "ticker": "2376",
    "name": "技嘉",
    "market": "TWSE",
    "yfinance": "2376.TW",
    "bloomberg": "2376 TT",
    "group": "AI 伺服器",
    "role": "LAGGARD"
  },
  {
    "ticker": "2356",
    "name": "英業達",
    "market": "TWSE",
    "yfinance": "2356.TW",
    "bloomberg": "2356 TT",
    "group": "AI 伺服器",
    "role": "PEER"
  },
  {
    "ticker": "8210",
    "name": "勤誠",
    "market": "TWSE",
    "yfinance": "8210.TW",
    "bloomberg": "8210 TT",
    "group": "AI 伺服器",
    "role": "PEER"
  },
  {
    "ticker": "2603",
    "name": "長榮",
    "market": "TWSE",
    "yfinance": "2603.TW",
    "bloomberg": "2603 TT",
    "group": "貨櫃航運",
    "role": "LEADER"
  },
  {
    "ticker": "2609",
    "name": "陽明",
    "market": "TWSE",
    "yfinance": "2609.TW",
    "bloomberg": "2609 TT",
    "group": "貨櫃航運",
    "role": "PEER"
  },
  {
    "ticker": "2615",
    "name": "萬海",
    "market": "TWSE",
    "yfinance": "2615.TW",
    "bloomberg": "2615 TT",
    "group": "貨櫃航運",
    "role": "LAGGARD"
  },
  {
    "ticker": "2881",
    "name": "富邦金",
    "market": "TWSE",
    "yfinance": "2881.TW",
    "bloomberg": "2881 TT",
    "group": "金融",
    "role": "LEADER"
  },
  {
    "ticker": "2882",
    "name": "國泰金",
    "market": "TWSE",
    "yfinance": "2882.TW",
    "bloomberg": "2882 TT",
    "group": "金融",
    "role": "PEER"
  },
  {
    "ticker": "2886",
    "name": "兆豐金",
    "market": "TWSE",
    "yfinance": "2886.TW",
    "bloomberg": "2886 TT",
    "group": "金融",
    "role": "PEER"
  },
  {
    "ticker": "2884",
    "name": "玉山金",
    "market": "TWSE",
    "yfinance": "2884.TW",
    "bloomberg": "2884 TT",
    "group": "金融",
    "role": "LAGGARD"
  },
  {
    "ticker": "2327",
    "name": "國巨",
    "market": "TWSE",
    "yfinance": "2327.TW",
    "bloomberg": "2327 TT",
    "group": "被動元件",
    "role": "LEADER"
  },
  {
    "ticker": "2492",
    "name": "華新科",
    "market": "TWSE",
    "yfinance": "2492.TW",
    "bloomberg": "2492 TT",
    "group": "被動元件",
    "role": "PEER"
  },
  {
    "ticker": "3026",
    "name": "禾伸堂",
    "market": "TPEX",
    "yfinance": "3026.TWO",
    "bloomberg": "3026 TT",
    "group": "被動元件",
    "role": "LAGGARD"
  },
  {
    "ticker": "6173",
    "name": "信昌電",
    "market": "TPEX",
    "yfinance": "6173.TWO",
    "bloomberg": "6173 TT",
    "group": "被動元件",
    "role": "PEER"
  },
  {
    "ticker": "3008",
    "name": "大立光",
    "market": "TWSE",
    "yfinance": "3008.TW",
    "bloomberg": "3008 TT",
    "group": "光學",
    "role": "LEADER"
  },
  {
    "ticker": "3406",
    "name": "玉晶光",
    "market": "TWSE",
    "yfinance": "3406.TW",
    "bloomberg": "3406 TT",
    "group": "光學",
    "role": "PEER"
  },
  {
    "ticker": "3019",
    "name": "亞光",
    "market": "TWSE",
    "yfinance": "3019.TW",
    "bloomberg": "3019 TT",
    "group": "光學",
    "role": "LAGGARD"
  },
  {
    "ticker": "3362",
    "name": "先進光",
    "market": "TWSE",
    "yfinance": "3362.TW",
    "bloomberg": "3362 TT",
    "group": "光學",
    "role": "PEER"
  },
  {
    "ticker": "2049",
    "name": "上銀",
    "market": "TWSE",
    "yfinance": "2049.TW",
    "bloomberg": "2049 TT",
    "group": "機器人",
    "role": "LEADER"
  },
  {
    "ticker": "2308",
    "name": "台達電",
    "market": "TWSE",
    "yfinance": "2308.TW",
    "bloomberg": "2308 TT",
    "group": "機器人",
    "role": "PEER"
  },
  {
    "ticker": "2359",
    "name": "所羅門",
    "market": "TWSE",
    "yfinance": "2359.TW",
    "bloomberg": "2359 TT",
    "group": "機器人",
    "role": "PEER"
  },
  {
    "ticker": "1597",
    "name": "直得",
    "market": "TPEX",
    "yfinance": "1597.TWO",
    "bloomberg": "1597 TT",
    "group": "機器人",
    "role": "LAGGARD"
  },
  {
    "ticker": "1590",
    "name": "亞德客-KY",
    "market": "TWSE",
    "yfinance": "1590.TW",
    "bloomberg": "1590 TT",
    "group": "機器人",
    "role": "LEADER"
  },
  {
    "ticker": "2464",
    "name": "盟立",
    "market": "TWSE",
    "yfinance": "2464.TW",
    "bloomberg": "2464 TT",
    "group": "機器人",
    "role": "PEER"
  },
  {
    "ticker": "3324",
    "name": "雙鴻",
    "market": "TWSE",
    "yfinance": "3324.TW",
    "bloomberg": "3324 TT",
    "group": "散熱",
    "role": "LEADER"
  },
  {
    "ticker": "3017",
    "name": "奇鋐",
    "market": "TWSE",
    "yfinance": "3017.TW",
    "bloomberg": "3017 TT",
    "group": "散熱",
    "role": "LEADER"
  },
  {
    "ticker": "2421",
    "name": "建準",
    "market": "TWSE",
    "yfinance": "2421.TW",
    "bloomberg": "2421 TT",
    "group": "散熱",
    "role": "PEER"
  },
  {
    "ticker": "3338",
    "name": "泰碩",
    "market": "TPEX",
    "yfinance": "3338.TWO",
    "bloomberg": "3338 TT",
    "group": "散熱",
    "role": "LAGGARD"
  },
  {
    "ticker": "6275",
    "name": "元山",
    "market": "TPEX",
    "yfinance": "6275.TWO",
    "bloomberg": "6275 TT",
    "group": "散熱",
    "role": "PEER"
  },
  {
    "ticker": "3483",
    "name": "力致",
    "market": "TWSE",
    "yfinance": "3483.TW",
    "bloomberg": "3483 TT",
    "group": "散熱",
    "role": "PEER"
  },
  {
    "ticker": "6591",
    "name": "動力-KY",
    "market": "TWSE",
    "yfinance": "6591.TW",
    "bloomberg": "6591 TT",
    "group": "散熱",
    "role": "PEER"
  },
  {
    "ticker": "6125",
    "name": "廣運",
    "market": "TWSE",
    "yfinance": "6125.TW",
    "bloomberg": "6125 TT",
    "group": "散熱",
    "role": "LAGGARD"
  },
  {
    "ticker": "4931",
    "name": "新盛力",
    "market": "TWSE",
    "yfinance": "4931.TW",
    "bloomberg": "4931 TT",
    "group": "BBU 備援電池",
    "role": "LEADER"
  },
  {
    "ticker": "6781",
    "name": "AES-KY",
    "market": "TWSE",
    "yfinance": "6781.TW",
    "bloomberg": "6781 TT",
    "group": "BBU 備援電池",
    "role": "PEER"
  },
  {
    "ticker": "3323",
    "name": "加百裕",
    "market": "TWSE",
    "yfinance": "3323.TW",
    "bloomberg": "3323 TT",
    "group": "BBU 備援電池",
    "role": "PEER"
  },
  {
    "ticker": "3211",
    "name": "順達",
    "market": "TWSE",
    "yfinance": "3211.TW",
    "bloomberg": "3211 TT",
    "group": "BBU 備援電池",
    "role": "LAGGARD"
  },
  {
    "ticker": "3081",
    "name": "聯亞",
    "market": "TPEX",
    "yfinance": "3081.TWO",
    "bloomberg": "3081 TT",
    "group": "CPO 共封裝光學",
    "role": "LEADER"
  },
  {
    "ticker": "6442",
    "name": "光聖",
    "market": "TPEX",
    "yfinance": "6442.TWO",
    "bloomberg": "6442 TT",
    "group": "CPO 共封裝光學",
    "role": "PEER"
  },
  {
    "ticker": "3363",
    "name": "上詮",
    "market": "TWSE",
    "yfinance": "3363.TW",
    "bloomberg": "3363 TT",
    "group": "CPO 共封裝光學",
    "role": "PEER"
  },
  {
    "ticker": "4979",
    "name": "華星光",
    "market": "TPEX",
    "yfinance": "4979.TWO",
    "bloomberg": "4979 TT",
    "group": "CPO 共封裝光學",
    "role": "LAGGARD"
  },
  {
    "ticker": "3163",
    "name": "波若威",
    "market": "TPEX",
    "yfinance": "3163.TWO",
    "bloomberg": "3163 TT",
    "group": "CPO 共封裝光學",
    "role": "PEER"
  },
  {
    "ticker": "4977",
    "name": "眾達-KY",
    "market": "TPEX",
    "yfinance": "4977.TWO",
    "bloomberg": "4977 TT",
    "group": "CPO 共封裝光學",
    "role": "PEER"
  },
  {
    "ticker": "3491",
    "name": "昇達科",
    "market": "TPEX",
    "yfinance": "3491.TWO",
    "bloomberg": "3491 TT",
    "group": "低軌衛星",
    "role": "LEADER"
  },
  {
    "ticker": "2314",
    "name": "台揚",
    "market": "TWSE",
    "yfinance": "2314.TW",
    "bloomberg": "2314 TT",
    "group": "低軌衛星",
    "role": "PEER"
  },
  {
    "ticker": "6285",
    "name": "啟碁",
    "market": "TWSE",
    "yfinance": "6285.TW",
    "bloomberg": "6285 TT",
    "group": "低軌衛星",
    "role": "PEER"
  },
  {
    "ticker": "6271",
    "name": "同欣電",
    "market": "TWSE",
    "yfinance": "6271.TW",
    "bloomberg": "6271 TT",
    "group": "低軌衛星",
    "role": "LAGGARD"
  },
  {
    "ticker": "2637",
    "name": "慧洋-KY",
    "market": "TWSE",
    "yfinance": "2637.TW",
    "bloomberg": "2637 TT",
    "group": "散裝航運",
    "role": "LEADER"
  },
  {
    "ticker": "2606",
    "name": "裕民",
    "market": "TWSE",
    "yfinance": "2606.TW",
    "bloomberg": "2606 TT",
    "group": "散裝航運",
    "role": "PEER"
  },
  {
    "ticker": "2605",
    "name": "新興",
    "market": "TWSE",
    "yfinance": "2605.TW",
    "bloomberg": "2605 TT",
    "group": "散裝航運",
    "role": "PEER"
  },
  {
    "ticker": "5608",
    "name": "四維航",
    "market": "TWSE",
    "yfinance": "5608.TW",
    "bloomberg": "5608 TT",
    "group": "散裝航運",
    "role": "LAGGARD"
  },
  {
    "ticker": "2612",
    "name": "中航",
    "market": "TWSE",
    "yfinance": "2612.TW",
    "bloomberg": "2612 TT",
    "group": "散裝航運",
    "role": "PEER"
  },
  {
    "ticker": "2617",
    "name": "台航",
    "market": "TWSE",
    "yfinance": "2617.TW",
    "bloomberg": "2617 TT",
    "group": "散裝航運",
    "role": "PEER"
  },
  {
    "ticker": "2641",
    "name": "正德",
    "market": "TWSE",
    "yfinance": "2641.TW",
    "bloomberg": "2641 TT",
    "group": "散裝航運",
    "role": "LAGGARD"
  },
  {
    "ticker": "2618",
    "name": "長榮航",
    "market": "TWSE",
    "yfinance": "2618.TW",
    "bloomberg": "2618 TT",
    "group": "航空",
    "role": "LEADER"
  },
  {
    "ticker": "2610",
    "name": "華航",
    "market": "TWSE",
    "yfinance": "2610.TW",
    "bloomberg": "2610 TT",
    "group": "航空",
    "role": "PEER"
  },
  {
    "ticker": "2646",
    "name": "星宇",
    "market": "TWSE",
    "yfinance": "2646.TW",
    "bloomberg": "2646 TT",
    "group": "航空",
    "role": "LAGGARD"
  },
  {
    "ticker": "2002",
    "name": "中鋼",
    "market": "TWSE",
    "yfinance": "2002.TW",
    "bloomberg": "2002 TT",
    "group": "鋼鐵",
    "role": "LEADER"
  },
  {
    "ticker": "2014",
    "name": "中鴻",
    "market": "TWSE",
    "yfinance": "2014.TW",
    "bloomberg": "2014 TT",
    "group": "鋼鐵",
    "role": "PEER"
  },
  {
    "ticker": "2023",
    "name": "燁輝",
    "market": "TWSE",
    "yfinance": "2023.TW",
    "bloomberg": "2023 TT",
    "group": "鋼鐵",
    "role": "PEER"
  },
  {
    "ticker": "2017",
    "name": "官田鋼",
    "market": "TWSE",
    "yfinance": "2017.TW",
    "bloomberg": "2017 TT",
    "group": "鋼鐵",
    "role": "LAGGARD"
  },
  {
    "ticker": "9957",
    "name": "燁聯",
    "market": "TWSE",
    "yfinance": "9957.TW",
    "bloomberg": "9957 TT",
    "group": "鋼鐵",
    "role": "PEER"
  },
  {
    "ticker": "2029",
    "name": "盛餘",
    "market": "TWSE",
    "yfinance": "2029.TW",
    "bloomberg": "2029 TT",
    "group": "鋼鐵",
    "role": "LAGGARD"
  },
  {
    "ticker": "2015",
    "name": "豐興",
    "market": "TWSE",
    "yfinance": "2015.TW",
    "bloomberg": "2015 TT",
    "group": "條鋼",
    "role": "LEADER"
  },
  {
    "ticker": "2006",
    "name": "東和鋼鐵",
    "market": "TWSE",
    "yfinance": "2006.TW",
    "bloomberg": "2006 TT",
    "group": "條鋼",
    "role": "PEER"
  },
  {
    "ticker": "2028",
    "name": "威致",
    "market": "TWSE",
    "yfinance": "2028.TW",
    "bloomberg": "2028 TT",
    "group": "條鋼",
    "role": "PEER"
  },
  {
    "ticker": "2012",
    "name": "春雨",
    "market": "TWSE",
    "yfinance": "2012.TW",
    "bloomberg": "2012 TT",
    "group": "條鋼",
    "role": "LAGGARD"
  },
  {
    "ticker": "1519",
    "name": "華城",
    "market": "TWSE",
    "yfinance": "1519.TW",
    "bloomberg": "1519 TT",
    "group": "重電",
    "role": "LEADER"
  },
  {
    "ticker": "1503",
    "name": "士電",
    "market": "TWSE",
    "yfinance": "1503.TW",
    "bloomberg": "1503 TT",
    "group": "重電",
    "role": "PEER"
  },
  {
    "ticker": "1513",
    "name": "中興電",
    "market": "TWSE",
    "yfinance": "1513.TW",
    "bloomberg": "1513 TT",
    "group": "重電",
    "role": "PEER"
  },
  {
    "ticker": "1514",
    "name": "亞力",
    "market": "TWSE",
    "yfinance": "1514.TW",
    "bloomberg": "1514 TT",
    "group": "重電",
    "role": "LAGGARD"
  },
  {
    "ticker": "1504",
    "name": "東元",
    "market": "TWSE",
    "yfinance": "1504.TW",
    "bloomberg": "1504 TT",
    "group": "重電",
    "role": "PEER"
  },
  {
    "ticker": "2371",
    "name": "大同",
    "market": "TWSE",
    "yfinance": "2371.TW",
    "bloomberg": "2371 TT",
    "group": "重電",
    "role": "PEER"
  },
  {
    "ticker": "2634",
    "name": "漢翔",
    "market": "TWSE",
    "yfinance": "2634.TW",
    "bloomberg": "2634 TT",
    "group": "軍工航太",
    "role": "LEADER"
  },
  {
    "ticker": "8033",
    "name": "雷虎",
    "market": "TWSE",
    "yfinance": "8033.TW",
    "bloomberg": "8033 TT",
    "group": "軍工航太",
    "role": "PEER"
  },
  {
    "ticker": "8222",
    "name": "寶一",
    "market": "TWSE",
    "yfinance": "8222.TW",
    "bloomberg": "8222 TT",
    "group": "軍工航太",
    "role": "PEER"
  },
  {
    "ticker": "8383",
    "name": "千附",
    "market": "TWSE",
    "yfinance": "8383.TW",
    "bloomberg": "8383 TT",
    "group": "軍工航太",
    "role": "LAGGARD"
  },
  {
    "ticker": "3037",
    "name": "欣興",
    "market": "TWSE",
    "yfinance": "3037.TW",
    "bloomberg": "3037 TT",
    "group": "ABF 載板",
    "role": "LEADER"
  },
  {
    "ticker": "8046",
    "name": "南電",
    "market": "TWSE",
    "yfinance": "8046.TW",
    "bloomberg": "8046 TT",
    "group": "ABF 載板",
    "role": "PEER"
  },
  {
    "ticker": "3189",
    "name": "景碩",
    "market": "TWSE",
    "yfinance": "3189.TW",
    "bloomberg": "3189 TT",
    "group": "ABF 載板",
    "role": "PEER"
  },
  {
    "ticker": "3167",
    "name": "大量",
    "market": "TPEX",
    "yfinance": "3167.TWO",
    "bloomberg": "3167 TT",
    "group": "ABF 載板",
    "role": "LAGGARD"
  },
  {
    "ticker": "2408",
    "name": "南亞科",
    "market": "TWSE",
    "yfinance": "2408.TW",
    "bloomberg": "2408 TT",
    "group": "記憶體",
    "role": "LEADER"
  },
  {
    "ticker": "2344",
    "name": "華邦電",
    "market": "TWSE",
    "yfinance": "2344.TW",
    "bloomberg": "2344 TT",
    "group": "記憶體",
    "role": "PEER"
  },
  {
    "ticker": "2337",
    "name": "旺宏",
    "market": "TWSE",
    "yfinance": "2337.TW",
    "bloomberg": "2337 TT",
    "group": "記憶體",
    "role": "PEER"
  },
  {
    "ticker": "8299",
    "name": "群聯",
    "market": "TPEX",
    "yfinance": "8299.TWO",
    "bloomberg": "8299 TT",
    "group": "記憶體",
    "role": "LAGGARD"
  },
  {
    "ticker": "3260",
    "name": "威剛",
    "market": "TWSE",
    "yfinance": "3260.TW",
    "bloomberg": "3260 TT",
    "group": "記憶體",
    "role": "PEER"
  },
  {
    "ticker": "2383",
    "name": "台光電",
    "market": "TWSE",
    "yfinance": "2383.TW",
    "bloomberg": "2383 TT",
    "group": "PCB",
    "role": "LEADER"
  },
  {
    "ticker": "4958",
    "name": "臻鼎-KY",
    "market": "TWSE",
    "yfinance": "4958.TW",
    "bloomberg": "4958 TT",
    "group": "PCB",
    "role": "LEADER"
  },
  {
    "ticker": "3044",
    "name": "健鼎",
    "market": "TWSE",
    "yfinance": "3044.TW",
    "bloomberg": "3044 TT",
    "group": "PCB",
    "role": "PEER"
  },
  {
    "ticker": "2368",
    "name": "金像電",
    "market": "TWSE",
    "yfinance": "2368.TW",
    "bloomberg": "2368 TT",
    "group": "PCB",
    "role": "PEER"
  },
  {
    "ticker": "2367",
    "name": "燿華",
    "market": "TWSE",
    "yfinance": "2367.TW",
    "bloomberg": "2367 TT",
    "group": "PCB",
    "role": "LAGGARD"
  },
  {
    "ticker": "6196",
    "name": "帆宣",
    "market": "TWSE",
    "yfinance": "6196.TW",
    "bloomberg": "6196 TT",
    "group": "台積電擴廠",
    "role": "LEADER"
  },
  {
    "ticker": "2404",
    "name": "漢唐",
    "market": "TWSE",
    "yfinance": "2404.TW",
    "bloomberg": "2404 TT",
    "group": "台積電擴廠",
    "role": "LEADER"
  },
  {
    "ticker": "6139",
    "name": "亞翔",
    "market": "TWSE",
    "yfinance": "6139.TW",
    "bloomberg": "6139 TT",
    "group": "台積電擴廠",
    "role": "PEER"
  },
  {
    "ticker": "6667",
    "name": "信紘科",
    "market": "TPEX",
    "yfinance": "6667.TWO",
    "bloomberg": "6667 TT",
    "group": "台積電擴廠",
    "role": "PEER"
  },
  {
    "ticker": "3413",
    "name": "京鼎",
    "market": "TPEX",
    "yfinance": "3413.TWO",
    "bloomberg": "3413 TT",
    "group": "台積電擴廠",
    "role": "PEER"
  },
  {
    "ticker": "3131",
    "name": "弘塑",
    "market": "TPEX",
    "yfinance": "3131.TWO",
    "bloomberg": "3131 TT",
    "group": "台積電擴廠",
    "role": "LAGGARD"
  },
  {
    "ticker": "6472",
    "name": "保瑞",
    "market": "TPEX",
    "yfinance": "6472.TWO",
    "bloomberg": "6472 TT",
    "group": "生技醫療",
    "role": "LEADER"
  },
  {
    "ticker": "6446",
    "name": "藥華藥",
    "market": "TWSE",
    "yfinance": "6446.TW",
    "bloomberg": "6446 TT",
    "group": "生技醫療",
    "role": "LEADER"
  },
  {
    "ticker": "1795",
    "name": "美時",
    "market": "TWSE",
    "yfinance": "1795.TW",
    "bloomberg": "1795 TT",
    "group": "生技醫療",
    "role": "PEER"
  },
  {
    "ticker": "4162",
    "name": "智擎",
    "market": "TPEX",
    "yfinance": "4162.TWO",
    "bloomberg": "4162 TT",
    "group": "生技醫療",
    "role": "LAGGARD"
  },
  {
    "ticker": "6562",
    "name": "聯亞藥",
    "market": "TPEX",
    "yfinance": "6562.TWO",
    "bloomberg": "6562 TT",
    "group": "生技醫療",
    "role": "LAGGARD"
  },
  {
    "ticker": "3034",
    "name": "聯詠",
    "market": "TWSE",
    "yfinance": "3034.TW",
    "bloomberg": "3034 TT",
    "group": "IC設計",
    "role": "LEADER"
  },
  {
    "ticker": "2379",
    "name": "瑞昱",
    "market": "TWSE",
    "yfinance": "2379.TW",
    "bloomberg": "2379 TT",
    "group": "IC設計",
    "role": "PEER"
  },
  {
    "ticker": "6415",
    "name": "矽力-KY",
    "market": "TWSE",
    "yfinance": "6415.TW",
    "bloomberg": "6415 TT",
    "group": "IC設計",
    "role": "PEER"
  },
  {
    "ticker": "3545",
    "name": "敦泰",
    "market": "TWSE",
    "yfinance": "3545.TW",
    "bloomberg": "3545 TT",
    "group": "IC設計",
    "role": "LAGGARD"
  },
  {
    "ticker": "2308",
    "name": "台達電",
    "market": "TWSE",
    "yfinance": "2308.TW",
    "bloomberg": "2308 TT",
    "group": "電源管理",
    "role": "LEADER"
  },
  {
    "ticker": "2301",
    "name": "光寶科",
    "market": "TWSE",
    "yfinance": "2301.TW",
    "bloomberg": "2301 TT",
    "group": "電源管理",
    "role": "PEER"
  },
  {
    "ticker": "3015",
    "name": "全漢",
    "market": "TWSE",
    "yfinance": "3015.TW",
    "bloomberg": "3015 TT",
    "group": "電源管理",
    "role": "PEER"
  },
  {
    "ticker": "5263",
    "name": "僑威",
    "market": "TPEX",
    "yfinance": "5263.TWO",
    "bloomberg": "5263 TT",
    "group": "電源管理",
    "role": "LAGGARD"
  },
  {
    "ticker": "3661",
    "name": "世芯-KY",
    "market": "TWSE",
    "yfinance": "3661.TW",
    "bloomberg": "3661 TT",
    "group": "ASIC 設計服務",
    "role": "LEADER"
  },
  {
    "ticker": "3443",
    "name": "創意",
    "market": "TWSE",
    "yfinance": "3443.TW",
    "bloomberg": "3443 TT",
    "group": "ASIC 設計服務",
    "role": "LEADER"
  },
  {
    "ticker": "3035",
    "name": "智原",
    "market": "TWSE",
    "yfinance": "3035.TW",
    "bloomberg": "3035 TT",
    "group": "ASIC 設計服務",
    "role": "PEER"
  },
  {
    "ticker": "2569",
    "name": "揚智",
    "market": "TWSE",
    "yfinance": "2569.TW",
    "bloomberg": "2569 TT",
    "group": "ASIC 設計服務",
    "role": "LAGGARD"
  },
  {
    "ticker": "3529",
    "name": "力旺",
    "market": "TPEX",
    "yfinance": "3529.TWO",
    "bloomberg": "3529 TT",
    "group": "矽智財 IP",
    "role": "LEADER"
  },
  {
    "ticker": "6533",
    "name": "晶心科",
    "market": "TPEX",
    "yfinance": "6533.TWO",
    "bloomberg": "6533 TT",
    "group": "矽智財 IP",
    "role": "PEER"
  },
  {
    "ticker": "6643",
    "name": "M31",
    "market": "TPEX",
    "yfinance": "6643.TWO",
    "bloomberg": "6643 TT",
    "group": "矽智財 IP",
    "role": "PEER"
  },
  {
    "ticker": "2345",
    "name": "智邦",
    "market": "TWSE",
    "yfinance": "2345.TW",
    "bloomberg": "2345 TT",
    "group": "網通設備",
    "role": "LEADER"
  },
  {
    "ticker": "3596",
    "name": "智易",
    "market": "TWSE",
    "yfinance": "3596.TW",
    "bloomberg": "3596 TT",
    "group": "網通設備",
    "role": "PEER"
  },
  {
    "ticker": "5388",
    "name": "中磊",
    "market": "TWSE",
    "yfinance": "5388.TW",
    "bloomberg": "5388 TT",
    "group": "網通設備",
    "role": "PEER"
  },
  {
    "ticker": "3380",
    "name": "明泰",
    "market": "TWSE",
    "yfinance": "3380.TW",
    "bloomberg": "3380 TT",
    "group": "網通設備",
    "role": "LAGGARD"
  },
  {
    "ticker": "3665",
    "name": "貿聯-KY",
    "market": "TWSE",
    "yfinance": "3665.TW",
    "bloomberg": "3665 TT",
    "group": "電動車",
    "role": "LEADER"
  },
  {
    "ticker": "1536",
    "name": "和大",
    "market": "TWSE",
    "yfinance": "1536.TW",
    "bloomberg": "1536 TT",
    "group": "電動車",
    "role": "PEER"
  },
  {
    "ticker": "2231",
    "name": "為升",
    "market": "TWSE",
    "yfinance": "2231.TW",
    "bloomberg": "2231 TT",
    "group": "電動車",
    "role": "PEER"
  },
  {
    "ticker": "8255",
    "name": "朋程",
    "market": "TPEX",
    "yfinance": "8255.TWO",
    "bloomberg": "8255 TT",
    "group": "電動車",
    "role": "LAGGARD"
  },
  {
    "ticker": "2731",
    "name": "雄獅",
    "market": "TWSE",
    "yfinance": "2731.TW",
    "bloomberg": "2731 TT",
    "group": "觀光餐飲",
    "role": "LEADER"
  },
  {
    "ticker": "2727",
    "name": "王品",
    "market": "TWSE",
    "yfinance": "2727.TW",
    "bloomberg": "2727 TT",
    "group": "觀光餐飲",
    "role": "LEADER"
  },
  {
    "ticker": "2729",
    "name": "瓦城",
    "market": "TWSE",
    "yfinance": "2729.TW",
    "bloomberg": "2729 TT",
    "group": "觀光餐飲",
    "role": "PEER"
  },
  {
    "ticker": "2707",
    "name": "晶華",
    "market": "TWSE",
    "yfinance": "2707.TW",
    "bloomberg": "2707 TT",
    "group": "觀光餐飲",
    "role": "PEER"
  },
  {
    "ticker": "5706",
    "name": "鳳凰",
    "market": "TWSE",
    "yfinance": "5706.TW",
    "bloomberg": "5706 TT",
    "group": "觀光餐飲",
    "role": "LAGGARD"
  },
  {
    "ticker": "2360",
    "name": "致茂",
    "market": "TWSE",
    "yfinance": "2360.TW",
    "bloomberg": "2360 TT",
    "group": "半導體設備",
    "role": "LEADER"
  },
  {
    "ticker": "3680",
    "name": "家登",
    "market": "TPEX",
    "yfinance": "3680.TWO",
    "bloomberg": "3680 TT",
    "group": "半導體設備",
    "role": "LEADER"
  },
  {
    "ticker": "3583",
    "name": "辛耘",
    "market": "TWSE",
    "yfinance": "3583.TW",
    "bloomberg": "3583 TT",
    "group": "半導體設備",
    "role": "PEER"
  },
  {
    "ticker": "6187",
    "name": "萬潤",
    "market": "TPEX",
    "yfinance": "6187.TWO",
    "bloomberg": "6187 TT",
    "group": "半導體設備",
    "role": "PEER"
  },
  {
    "ticker": "2467",
    "name": "志聖",
    "market": "TWSE",
    "yfinance": "2467.TW",
    "bloomberg": "2467 TT",
    "group": "半導體設備",
    "role": "LAGGARD"
  },
  {
    "ticker": "6690",
    "name": "安碁資訊",
    "market": "TPEX",
    "yfinance": "6690.TWO",
    "bloomberg": "6690 TT",
    "group": "資安/系統整合",
    "role": "LEADER"
  },
  {
    "ticker": "2480",
    "name": "敦陽科",
    "market": "TWSE",
    "yfinance": "2480.TW",
    "bloomberg": "2480 TT",
    "group": "資安/系統整合",
    "role": "PEER"
  },
  {
    "ticker": "6214",
    "name": "精誠",
    "market": "TPEX",
    "yfinance": "6214.TWO",
    "bloomberg": "6214 TT",
    "group": "資安/系統整合",
    "role": "PEER"
  },
  {
    "ticker": "3029",
    "name": "零壹",
    "market": "TWSE",
    "yfinance": "3029.TW",
    "bloomberg": "3029 TT",
    "group": "資安/系統整合",
    "role": "LAGGARD"
  }
];
export const ENG047_FRED = [
  {
    "seriesId": "U6RATE",
    "title": "廣義失業率 U6",
    "category": "Labor",
    "frequency": "M",
    "units": "Percent"
  },
  {
    "seriesId": "U4RATE",
    "title": "U4(含灰心勞工)",
    "category": "Labor",
    "frequency": "M",
    "units": "Percent"
  },
  {
    "seriesId": "U5RATE",
    "title": "U5(含邊際附著)",
    "category": "Labor",
    "frequency": "M",
    "units": "Percent"
  },
  {
    "seriesId": "EMRATIO",
    "title": "就業人口比",
    "category": "Labor",
    "frequency": "M",
    "units": "Percent"
  },
  {
    "seriesId": "LNS11300060",
    "title": "勞參率 25-54 主力齡",
    "category": "Labor",
    "frequency": "M",
    "units": "Percent"
  },
  {
    "seriesId": "CCSA",
    "title": "續領失業金",
    "category": "Labor",
    "frequency": "M",
    "units": "Percent"
  },
  {
    "seriesId": "UEMPLT5",
    "title": "失業 <5 週",
    "category": "Labor",
    "frequency": "M",
    "units": "Percent"
  },
  {
    "seriesId": "UEMP5TO14",
    "title": "失業 5-14 週",
    "category": "Labor",
    "frequency": "M",
    "units": "Percent"
  },
  {
    "seriesId": "UEMP15T26",
    "title": "失業 15-26 週",
    "category": "Labor",
    "frequency": "M",
    "units": "Percent"
  },
  {
    "seriesId": "UEMP27OV",
    "title": "失業 27 週以上",
    "category": "Labor",
    "frequency": "M",
    "units": "Percent"
  },
  {
    "seriesId": "UEMPMEAN",
    "title": "平均失業週數",
    "category": "Labor",
    "frequency": "M",
    "units": "Percent"
  },
  {
    "seriesId": "JTSJOR",
    "title": "職缺率(開缺率)",
    "category": "Labor",
    "frequency": "M",
    "units": "Percent"
  },
  {
    "seriesId": "JTSHIL",
    "title": "僱用數",
    "category": "Labor",
    "frequency": "M",
    "units": "Percent"
  },
  {
    "seriesId": "JTSHIR",
    "title": "僱用率",
    "category": "Labor",
    "frequency": "M",
    "units": "Percent"
  },
  {
    "seriesId": "JTSQUR",
    "title": "離職率(自願)",
    "category": "Labor",
    "frequency": "M",
    "units": "Percent"
  },
  {
    "seriesId": "CPIENGSL",
    "title": "CPI 能源",
    "category": "Inflation",
    "frequency": "M",
    "units": "Index"
  },
  {
    "seriesId": "CPIUFDSL",
    "title": "CPI 食物",
    "category": "Inflation",
    "frequency": "M",
    "units": "Index"
  },
  {
    "seriesId": "CPIMEDSL",
    "title": "CPI 醫療",
    "category": "Inflation",
    "frequency": "M",
    "units": "Index"
  },
  {
    "seriesId": "CPIAPPSL",
    "title": "CPI 服裝",
    "category": "Inflation",
    "frequency": "M",
    "units": "Index"
  },
  {
    "seriesId": "CORESTICKM159SFRBATL",
    "title": "黏性核心 CPI(Atlanta Fed)",
    "category": "Inflation",
    "frequency": "M",
    "units": "Percent"
  },
  {
    "seriesId": "MEDCPIM158SFRBCLE",
    "title": "中位數 CPI(Cleveland Fed)",
    "category": "Inflation",
    "frequency": "M",
    "units": "Index"
  }
] as const;

/** 利率／匯率／聯邦收支：FRED 可進湖；MTS 分項要 Treasury FiscalData 第二閘. */
export const MACRO_PLUS = [
  { seriesId: "DGS1MO", title: "1M 公債", category: "Rates", gate: "FRED" },
  { seriesId: "DTB3", title: "3M T-Bill", category: "Rates", gate: "FRED" },
  { seriesId: "DGS1", title: "1Y 公債", category: "Rates", gate: "FRED" },
  { seriesId: "DGS3", title: "3Y 公債", category: "Rates", gate: "FRED" },
  { seriesId: "DGS7", title: "7Y 公債", category: "Rates", gate: "FRED" },
  { seriesId: "DGS20", title: "20Y 公債", category: "Rates", gate: "FRED" },
  { seriesId: "IORB", title: "準備金利率", category: "Rates", gate: "FRED" },
  { seriesId: "T5YIE", title: "5Y 損益兩平通膨", category: "Rates", gate: "FRED" },
  { seriesId: "DEXUSEU", title: "USD/EUR", category: "FX", gate: "FRED" },
  { seriesId: "DEXJPUS", title: "JPY/USD", category: "FX", gate: "FRED" },
  { seriesId: "DEXUSUK", title: "USD/GBP", category: "FX", gate: "FRED" },
  { seriesId: "DEXKOUS", title: "KRW/USD", category: "FX", gate: "FRED" },
  { seriesId: "FGRECPT", title: "聯邦經常收入", category: "Fiscal", gate: "FRED" },
  { seriesId: "FGEXPND", title: "聯邦經常支出", category: "Fiscal", gate: "FRED" },
  { seriesId: "FYFSD", title: "聯邦盈餘／赤字", category: "Fiscal", gate: "FRED" },
  { seriesId: "GFDEBTN", title: "聯邦公債餘額", category: "Fiscal", gate: "FRED" },
  { seriesId: "GFDEGDQ188S", title: "債務／GDP", category: "Fiscal", gate: "FRED" },
  { seriesId: "WTREGEN", title: "TGA 國庫帳", category: "Fiscal", gate: "FRED" },
  { seriesId: "MTS.ReceiptsBySource", title: "稅收分項(所得／公司／關稅)", category: "Fiscal", gate: "Treasury_FD" },
  { seriesId: "MTS.OutlaysByFunction", title: "支出分項(國防／社保／醫療)", category: "Fiscal", gate: "Treasury_FD" },
] as const;

export const VDF_UNIFIED_PARAMS = {
  start: "2018-01-01",
  end: "TODAY",
  batch: 5,
  retries: 3,
  honesty: "no simulation masquerading as live",
} as const;
export const MOTHER_PACK = [
  { id: "CGC", file: "VIA_CentralGovernanceEngine.py", role: "本台唯一總管", used: true },
  { id: "SHELL", file: "CGC_MDL116_UnifiedShell", role: "左引擎＋分頁殼", used: true },
  { id: "DECK", file: "CGC_MDL095_DeckServer", role: "VDF/VRN/VAR 甲板", used: true },
  { id: "DOWN", file: "VIA_DownwardController.py", role: "總管向下啟動 VDF→VRN→VAR", used: true },
  { id: "PRIO", file: "VIA_FilePriorityRouter.py", role: "VRN I/O 優先序", used: true },
  { id: "ACCEL", file: "VIA_TestAccelerator.py", role: "PS20 搭配檢查", used: true },
  { id: "ENV", file: "VIA_EnvDeepProbe.py", role: "via_core / via_* 協調層", used: true },
  { id: "HARD", file: "VIA_EngineHardening.py", role: "全日曆測燈號", used: true },
  { id: "VER", file: "VIA_VersionGuard_v0110.ps1", role: "模組版本契約", used: true },
  { id: "TOOL", file: "VIA_ToolchainInstaller_v0100.ps1", role: "工具鏈安裝閘", used: true },
  { id: "LAUNCH", file: "VIA_Launch_NonBlocking_v0100.ps1", role: "非阻塞啟動", used: true },
  { id: "INTAKE", file: "CGC_MDL122_IntakeRoster", role: "VRN 進件清冊", used: true },
  { id: "MACRO", file: "VDF_Macro_Request_All_v0200.json", role: "FRED 冊＋ENG047 細目", used: true },
  { id: "RF", file: "VIA_TW10Y_AdaptiveRiskFree", role: "DGS10 無風險利率", used: true },
  { id: "CLASS", file: "VIA_SupportiveModules_Classifier", role: "加速器／網路分類", used: true },
  { id: "SAME", file: "VIA_SameNameConsolidator_v0110.ps1", role: "同名權威版 v0110", used: true },
  { id: "AUTH", file: "VIA_AuthorityAudit.py", role: "UI/湖權威", used: true },
  { id: "FINAUD", file: "VIA_VRN_FinancialRowAuditor.py", role: "財務列去重鑑測", used: true },
  { id: "PROF", file: "VIA_Profile_Doctor_v0100.ps1", role: "profile／env", used: true },
  { id: "POLY", file: "VIA_Polyglot_Repair_Injector_v0100.ps1", role: "多語橋注入", used: true },
  { id: "REC", file: "VIA_Recover_v0110.ps1", role: "隔離不刪", used: true },
  { id: "CONS", file: "VIA_CentralGovernanceConsole.py", role: "本台 HTML Console", used: true },
  { id: "R1", file: "VIA_Round1_CodeRepair_v0100.ps1", role: "Round1 只增不減", used: true },
] as const;

const byTicker = new Map(TW_UNIVERSE.map((m) => [m.ticker, m]));
export function lookupTw(core: string): TwMember | undefined {
  return byTicker.get(core);
}
export const TWSE_SET = new Set(TW_UNIVERSE.filter((m) => m.market === "TWSE").map((m) => m.ticker));
export const TPEX_SET = new Set(TW_UNIVERSE.filter((m) => m.market === "TPEX").map((m) => m.ticker));
export const TW_LEADERS = TW_UNIVERSE.filter((m) => m.role === "LEADER");

