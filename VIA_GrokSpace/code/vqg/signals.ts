export type SignalDef = {
  id: string;
  indicatorId: string;
  name: string;
  meaning: string;
  testQuestion: string;
  evidenceRule: string;
  noiseRule: string;
  saturationRule: string;
};

const ASK = "到目前這一筆，這個跡象是否成立？";
const NOISE = "這一筆的成立與否和前一筆不同，而且驅動它的數字仍在自身近 120 筆的 20 到 80 分位，記為潛在噪音。";
const OSC = "近 5 筆都在 70 以上或都在 30 以下，極差小於 8，價格仍往同一邊走，記為鈍化。鈍化只說明指標卡住，不表示價格會轉彎。";
const NONE = "不適用。這不是會停在極端區的震盪指標。";

export const SIGNALS: SignalDef[] = [
  {
    id: "VIA-VQG-SG-TRD001",
    indicatorId: "VIA-VQG-TA-TRD001",
    name: "收盤在 20 日均線之上",
    meaning: "調整後收盤高於 20 日簡單均線。這是目前的位置，不是進場訊號。",
    testQuestion: ASK,
    evidenceRule: "收盤大於 20 日簡單均線，記為看得到。",
    noiseRule: NOISE,
    saturationRule: NONE,
  },
  {
    id: "VIA-VQG-SG-TRD002",
    indicatorId: "VIA-VQG-TA-TRD001",
    name: "10 日均線在 60 日均線之上",
    meaning: "短均線目前在長均線之上。上下關係換邊只說明這一筆和前一筆不同，不叫買賣交叉。",
    testQuestion: ASK,
    evidenceRule: "10 日簡單均線大於 60 日簡單均線，記為看得到。",
    noiseRule: NOISE,
    saturationRule: NONE,
  },
  {
    id: "VIA-VQG-SG-TRD003",
    indicatorId: "VIA-VQG-TA-TRD002",
    name: "收盤在 20 日指數均線之上",
    meaning: "調整後收盤高於 20 日指數均線。",
    testQuestion: ASK,
    evidenceRule: "收盤大於 20 日指數均線，記為看得到。",
    noiseRule: NOISE,
    saturationRule: NONE,
  },
  {
    id: "VIA-VQG-SG-VOL001",
    indicatorId: "VIA-VQG-TA-TRD003",
    name: "布林帶寬在自身低位",
    meaning: "20 日、2 倍標準差的帶寬，落在自身近 120 筆的低位。低位只說明通道較窄，不表示即將突破。",
    testQuestion: ASK,
    evidenceRule: "帶寬的自身分位在 20 以下，記為看得到。",
    noiseRule: NOISE,
    saturationRule: NONE,
  },
  {
    id: "VIA-VQG-SG-MOM001",
    indicatorId: "VIA-VQG-TA-MOM001",
    name: "RSI 在自身高位",
    meaning: "14 日 RSI 落在自身近 120 筆的高位。不用 70 當作固定買賣點。",
    testQuestion: ASK,
    evidenceRule: "RSI 的自身分位在 80 以上，記為看得到。",
    noiseRule: NOISE,
    saturationRule: OSC,
  },
  {
    id: "VIA-VQG-SG-MOM002",
    indicatorId: "VIA-VQG-TA-MOM001",
    name: "RSI 在自身低位",
    meaning: "14 日 RSI 落在自身近 120 筆的低位。不用 30 當作固定買賣點。",
    testQuestion: ASK,
    evidenceRule: "RSI 的自身分位在 20 以下，記為看得到。",
    noiseRule: NOISE,
    saturationRule: OSC,
  },
  {
    id: "VIA-VQG-SG-MOM003",
    indicatorId: "VIA-VQG-TA-MOM001",
    name: "RSI 鈍化",
    meaning: "RSI 停在極端區，價格還在往同一邊走，指標幾乎不再跟著走。",
    testQuestion: ASK,
    evidenceRule: "符合鈍化規則，記為看得到。",
    noiseRule: "鈍化這個跡象本身不用中間區翻轉來記噪音。",
    saturationRule: OSC,
  },
  {
    id: "VIA-VQG-SG-MOM004",
    indicatorId: "VIA-VQG-TA-MOM002",
    name: "MACD 柱為正",
    meaning: "柱狀值為正，表示快線目前在慢線之上。正負換邊只記載這一筆的狀態。",
    testQuestion: ASK,
    evidenceRule: "12、26、9 的柱狀值大於 0，記為看得到。",
    noiseRule: NOISE,
    saturationRule: NONE,
  },
  {
    id: "VIA-VQG-SG-MOM005",
    indicatorId: "VIA-VQG-TA-MOM003",
    name: "K 在 D 之上",
    meaning: "9 日 KDJ 的 K 目前高於 D。這不是黃金交叉的交易指令。",
    testQuestion: ASK,
    evidenceRule: "K 大於 D，記為看得到。",
    noiseRule: NOISE,
    saturationRule: OSC,
  },
  {
    id: "VIA-VQG-SG-MOM006",
    indicatorId: "VIA-VQG-TA-MOM003",
    name: "K 鈍化",
    meaning: "K 停在極端區，價格還在往同一邊走，K 幾乎不再跟著走。最高等於最低的日子不拿來湊鈍化。",
    testQuestion: ASK,
    evidenceRule: "符合鈍化規則，記為看得到。",
    noiseRule: "鈍化這個跡象本身不用中間區翻轉來記噪音。",
    saturationRule: OSC,
  },
  {
    id: "VIA-VQG-SG-TRD004",
    indicatorId: "VIA-VQG-TA-TRD003",
    name: "收盤在布林上軌之外",
    meaning: "調整後收盤高於 20 日、2 倍、ddof 為 0 的上軌。在軌外只說明位置，不表示會拉回。",
    testQuestion: ASK,
    evidenceRule: "收盤大於上軌，記為看得到。",
    noiseRule: NOISE,
    saturationRule: NONE,
  },
  {
    id: "VIA-VQG-SG-TRD005",
    indicatorId: "VIA-VQG-TA-TRD003",
    name: "收盤在布林下軌之外",
    meaning: "調整後收盤低於同一組布林下軌。在軌外只說明位置，不表示會彈回。",
    testQuestion: ASK,
    evidenceRule: "收盤小於下軌，記為看得到。",
    noiseRule: NOISE,
    saturationRule: NONE,
  },
  {
    id: "VIA-VQG-SG-MOM007",
    indicatorId: "VIA-VQG-TA-MOM004",
    name: "20 日漲跌為正",
    meaning: "調整後收盤相對 20 個交易日前為正。這是已發生的區間變化，不是趨勢預測。",
    testQuestion: ASK,
    evidenceRule: "20 日漲跌幅大於 0，記為看得到。",
    noiseRule: NOISE,
    saturationRule: NONE,
  },
];
