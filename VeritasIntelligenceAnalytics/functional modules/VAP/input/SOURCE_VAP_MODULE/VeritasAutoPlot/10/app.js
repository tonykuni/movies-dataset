/* eslint-disable no-unused-vars */
(function () {
  "use strict";

  // ========================================
  // Monthly oil price data (EIA U.S. Crude Oil First Purchase Price, $/barrel)
  // Source: https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?n=pet&s=f000000__3&f=m
  // WTI Spot from 1986+: https://www.eia.gov/dnav/pet/hist/rwtcm.htm
  // ========================================
  const rawData = [
    // 1975
    ["1975-01",7.61],["1975-02",7.47],["1975-03",7.57],["1975-04",7.55],["1975-05",7.52],["1975-06",7.49],
    ["1975-07",7.75],["1975-08",7.73],["1975-09",7.75],["1975-10",7.83],["1975-11",7.80],["1975-12",7.93],
    // 1976
    ["1976-01",8.63],["1976-02",7.91],["1976-03",7.78],["1976-04",7.86],["1976-05",7.89],["1976-06",8.00],
    ["1976-07",8.04],["1976-08",8.03],["1976-09",8.39],["1976-10",8.46],["1976-11",8.61],["1976-12",8.62],
    // 1977
    ["1977-01",8.50],["1977-02",8.56],["1977-03",8.45],["1977-04",8.41],["1977-05",8.49],["1977-06",8.44],
    ["1977-07",8.47],["1977-08",8.45],["1977-09",8.43],["1977-10",8.72],["1977-11",8.69],["1977-12",8.81],
    // 1978
    ["1978-01",8.71],["1978-02",8.86],["1978-03",8.80],["1978-04",8.82],["1978-05",8.81],["1978-06",9.05],
    ["1978-07",8.96],["1978-08",9.05],["1978-09",9.15],["1978-10",9.17],["1978-11",9.20],["1978-12",9.47],
    // 1979
    ["1979-01",9.46],["1979-02",9.69],["1979-03",9.83],["1979-04",10.33],["1979-05",10.71],["1979-06",11.70],
    ["1979-07",13.39],["1979-08",14.00],["1979-09",14.57],["1979-10",15.06],["1979-11",15.52],["1979-12",17.00],
    // 1980
    ["1980-01",17.86],["1980-02",18.86],["1980-03",19.33],["1980-04",20.28],["1980-05",21.05],["1980-06",21.52],
    ["1980-07",22.31],["1980-08",22.62],["1980-09",22.59],["1980-10",23.23],["1980-11",23.99],["1980-12",25.83],
    // 1981
    ["1981-01",28.81],["1981-02",34.30],["1981-03",34.59],["1981-04",33.92],["1981-05",32.73],["1981-06",31.68],
    ["1981-07",31.10],["1981-08",31.10],["1981-09",31.10],["1981-10",30.98],["1981-11",30.97],["1981-12",30.80],
    // 1982
    ["1982-01",30.80],["1982-02",29.73],["1982-03",28.31],["1982-04",27.64],["1982-05",27.66],["1982-06",28.12],
    ["1982-07",28.09],["1982-08",27.99],["1982-09",27.99],["1982-10",28.76],["1982-11",28.74],["1982-12",28.02],
    // 1983
    ["1983-01",27.22],["1983-02",26.41],["1983-03",26.08],["1983-04",25.85],["1983-05",26.08],["1983-06",25.98],
    ["1983-07",25.86],["1983-08",26.03],["1983-09",26.08],["1983-10",26.04],["1983-11",26.09],["1983-12",25.88],
    // 1984
    ["1984-01",25.93],["1984-02",26.06],["1984-03",26.05],["1984-04",25.93],["1984-05",26.00],["1984-06",26.09],
    ["1984-07",26.11],["1984-08",26.02],["1984-09",25.97],["1984-10",25.92],["1984-11",25.44],["1984-12",25.05],
    // 1985
    ["1985-01",24.26],["1985-02",23.64],["1985-03",23.89],["1985-04",24.19],["1985-05",24.18],["1985-06",24.07],
    ["1985-07",24.04],["1985-08",23.99],["1985-09",23.96],["1985-10",24.10],["1985-11",24.27],["1985-12",24.51],
    // 1986
    ["1986-01",23.12],["1986-02",17.65],["1986-03",12.62],["1986-04",10.68],["1986-05",10.75],["1986-06",10.68],
    ["1986-07",9.25],["1986-08",9.77],["1986-09",11.09],["1986-10",11.00],["1986-11",11.05],["1986-12",11.73],
    // 1987
    ["1987-01",13.79],["1987-02",14.51],["1987-03",14.54],["1987-04",14.95],["1987-05",15.29],["1987-06",15.95],
    ["1987-07",16.88],["1987-08",17.06],["1987-09",16.25],["1987-10",15.95],["1987-11",15.46],["1987-12",14.27],
    // 1988
    ["1988-01",13.64],["1988-02",13.43],["1988-03",12.96],["1988-04",13.92],["1988-05",14.12],["1988-06",13.59],
    ["1988-07",12.38],["1988-08",12.22],["1988-09",11.63],["1988-10",10.62],["1988-11",10.31],["1988-12",11.99],
    // 1989
    ["1989-01",13.80],["1989-02",14.24],["1989-03",15.65],["1989-04",17.04],["1989-05",16.76],["1989-06",16.42],
    ["1989-07",16.32],["1989-08",15.01],["1989-09",15.58],["1989-10",16.25],["1989-11",16.30],["1989-12",17.01],
    // 1990
    ["1990-01",18.49],["1990-02",18.16],["1990-03",16.57],["1990-04",14.52],["1990-05",13.82],["1990-06",12.79],
    ["1990-07",14.03],["1990-08",21.87],["1990-09",28.46],["1990-10",30.86],["1990-11",27.53],["1990-12",22.63],
    // 1991
    ["1991-01",19.60],["1991-02",16.28],["1991-03",15.13],["1991-04",16.16],["1991-05",16.44],["1991-06",15.58],
    ["1991-07",16.36],["1991-08",16.60],["1991-09",16.71],["1991-10",17.72],["1991-11",17.12],["1991-12",14.68],
    // 1992
    ["1992-01",13.99],["1992-02",14.04],["1992-03",14.12],["1992-04",15.36],["1992-05",16.38],["1992-06",17.96],
    ["1992-07",17.80],["1992-08",17.07],["1992-09",17.20],["1992-10",17.16],["1992-11",16.00],["1992-12",14.94],
    // 1993
    ["1993-01",14.70],["1993-02",15.53],["1993-03",15.94],["1993-04",16.15],["1993-05",16.03],["1993-06",15.06],
    ["1993-07",13.83],["1993-08",13.75],["1993-09",13.39],["1993-10",16.27],["1993-11",15.21],["1993-12",12.95],
    // 1994
    ["1994-01",10.49],["1994-02",10.71],["1994-03",10.94],["1994-04",12.31],["1994-05",14.02],["1994-06",14.93],
    ["1994-07",15.34],["1994-08",14.50],["1994-09",13.62],["1994-10",13.84],["1994-11",14.14],["1994-12",13.43],
    // 1995
    ["1995-01",14.00],["1995-02",14.71],["1995-03",14.68],["1995-04",15.84],["1995-05",15.85],["1995-06",15.02],
    ["1995-07",14.01],["1995-08",14.13],["1995-09",14.49],["1995-10",13.68],["1995-11",14.03],["1995-12",15.02],
    // 1996
    ["1996-01",15.43],["1996-02",15.54],["1996-03",17.63],["1996-04",19.58],["1996-05",17.94],["1996-06",16.94],
    ["1996-07",17.63],["1996-08",18.29],["1996-09",19.93],["1996-10",21.09],["1996-11",20.20],["1996-12",21.34],
    // 1997
    ["1997-01",21.76],["1997-02",19.38],["1997-03",17.83],["1997-04",16.63],["1997-05",17.23],["1997-06",15.88],
    ["1997-07",15.89],["1997-08",16.19],["1997-09",16.41],["1997-10",17.66],["1997-11",16.83],["1997-12",15.04],
    // 1998
    ["1998-01",13.45],["1998-02",12.17],["1998-03",11.15],["1998-04",11.28],["1998-05",11.13],["1998-06",10.00],
    ["1998-07",10.44],["1998-08",10.20],["1998-09",11.29],["1998-10",11.32],["1998-11",9.64],["1998-12",8.03],
    // 1999
    ["1999-01",8.57],["1999-02",8.60],["1999-03",10.76],["1999-04",12.82],["1999-05",13.92],["1999-06",14.39],
    ["1999-07",16.12],["1999-08",17.58],["1999-09",20.03],["1999-10",19.71],["1999-11",21.35],["1999-12",22.55],
    // 2000
    ["2000-01",23.53],["2000-02",25.48],["2000-03",26.19],["2000-04",23.20],["2000-05",25.58],["2000-06",27.62],
    ["2000-07",26.81],["2000-08",27.91],["2000-09",29.72],["2000-10",29.65],["2000-11",30.36],["2000-12",24.46],
    // 2001
    ["2001-01",24.64],["2001-02",25.27],["2001-03",22.98],["2001-04",23.39],["2001-05",24.06],["2001-06",23.43],
    ["2001-07",22.82],["2001-08",23.08],["2001-09",22.37],["2001-10",18.73],["2001-11",16.40],["2001-12",15.54],
    // 2002
    ["2002-01",15.89],["2002-02",16.93],["2002-03",20.28],["2002-04",22.52],["2002-05",23.51],["2002-06",22.59],
    ["2002-07",23.51],["2002-08",24.76],["2002-09",26.08],["2002-10",25.29],["2002-11",23.38],["2002-12",25.29],
    // 2003
    ["2003-01",28.42],["2003-02",31.85],["2003-03",30.10],["2003-04",25.45],["2003-05",24.95],["2003-06",26.84],
    ["2003-07",27.52],["2003-08",27.94],["2003-09",25.23],["2003-10",26.53],["2003-11",27.21],["2003-12",28.53],
    // 2004
    ["2004-01",30.35],["2004-02",31.21],["2004-03",32.86],["2004-04",33.20],["2004-05",35.73],["2004-06",34.53],
    ["2004-07",36.54],["2004-08",40.10],["2004-09",40.56],["2004-10",46.14],["2004-11",42.85],["2004-12",38.22],
    // 2005
    ["2005-01",40.18],["2005-02",42.19],["2005-03",47.56],["2005-04",47.26],["2005-05",44.03],["2005-06",49.83],
    ["2005-07",53.35],["2005-08",58.90],["2005-09",59.64],["2005-10",56.99],["2005-11",53.20],["2005-12",53.24],
    // 2006
    ["2006-01",57.85],["2006-02",55.69],["2006-03",55.64],["2006-04",62.52],["2006-05",64.40],["2006-06",64.65],
    ["2006-07",67.71],["2006-08",67.21],["2006-09",59.37],["2006-10",53.26],["2006-11",52.42],["2006-12",55.03],
    // 2007
    ["2007-01",49.32],["2007-02",52.94],["2007-03",54.95],["2007-04",58.20],["2007-05",58.90],["2007-06",62.35],
    ["2007-07",69.23],["2007-08",67.77],["2007-09",73.27],["2007-10",79.32],["2007-11",87.16],["2007-12",85.28],
    // 2008
    ["2008-01",87.06],["2008-02",89.41],["2008-03",98.44],["2008-04",106.64],["2008-05",118.55],["2008-06",127.47],
    ["2008-07",128.08],["2008-08",112.83],["2008-09",98.50],["2008-10",73.18],["2008-11",53.67],["2008-12",36.80],
    // 2009
    ["2009-01",35.00],["2009-02",34.14],["2009-03",42.45],["2009-04",45.19],["2009-05",52.67],["2009-06",63.09],
    ["2009-07",60.44],["2009-08",65.28],["2009-09",65.28],["2009-10",69.82],["2009-11",71.99],["2009-12",70.42],
    // 2010
    ["2010-01",72.87],["2010-02",72.74],["2010-03",75.77],["2010-04",78.80],["2010-05",70.91],["2010-06",70.77],
    ["2010-07",71.37],["2010-08",72.07],["2010-09",71.23],["2010-10",76.02],["2010-11",79.20],["2010-12",83.98],
    // 2011
    ["2011-01",85.66],["2011-02",86.69],["2011-03",99.19],["2011-04",108.80],["2011-05",102.46],["2011-06",97.30],
    ["2011-07",97.82],["2011-08",89.00],["2011-09",90.22],["2011-10",92.28],["2011-11",100.18],["2011-12",98.71],
    // 2012
    ["2012-01",98.99],["2012-02",102.04],["2012-03",105.42],["2012-04",103.62],["2012-05",95.57],["2012-06",83.59],
    ["2012-07",86.10],["2012-08",92.53],["2012-09",95.98],["2012-10",92.24],["2012-11",89.64],["2012-12",89.81],
    // 2013
    ["2013-01",95.00],["2013-02",95.01],["2013-03",95.54],["2013-04",94.41],["2013-05",94.75],["2013-06",93.82],
    ["2013-07",101.41],["2013-08",102.96],["2013-09",102.32],["2013-10",96.18],["2013-11",88.70],["2013-12",91.85],
    // 2014
    ["2014-01",89.57],["2014-02",96.86],["2014-03",96.17],["2014-04",96.49],["2014-05",95.74],["2014-06",98.68],
    ["2014-07",96.70],["2014-08",90.72],["2014-09",86.87],["2014-10",78.84],["2014-11",71.07],["2014-12",54.86],
    // 2015
    ["2015-01",43.06],["2015-02",44.35],["2015-03",42.66],["2015-04",49.30],["2015-05",54.38],["2015-06",55.88],
    ["2015-07",47.70],["2015-08",39.98],["2015-09",41.60],["2015-10",42.34],["2015-11",38.19],["2015-12",32.26],
    // 2016
    ["2016-01",27.02],["2016-02",25.52],["2016-03",31.87],["2016-04",35.59],["2016-05",41.02],["2016-06",43.96],
    ["2016-07",40.71],["2016-08",40.46],["2016-09",40.55],["2016-10",45.00],["2016-11",41.65],["2016-12",47.12],
    // 2017
    ["2017-01",48.19],["2017-02",49.41],["2017-03",46.39],["2017-04",47.23],["2017-05",45.19],["2017-06",42.17],
    ["2017-07",43.42],["2017-08",44.96],["2017-09",47.17],["2017-10",49.12],["2017-11",55.19],["2017-12",56.98],
    // 2018
    ["2018-01",62.25],["2018-02",61.18],["2018-03",60.68],["2018-04",63.50],["2018-05",66.16],["2018-06",62.80],
    ["2018-07",67.00],["2018-08",62.64],["2018-09",63.54],["2018-10",65.18],["2018-11",55.65],["2018-12",47.63],
    // 2019
    ["2019-01",48.00],["2019-02",52.60],["2019-03",57.46],["2019-04",63.00],["2019-05",59.73],["2019-06",54.34],
    ["2019-07",56.47],["2019-08",53.63],["2019-09",55.14],["2019-10",53.14],["2019-11",54.96],["2019-12",58.41],
    // 2020
    ["2020-01",56.55],["2020-02",49.66],["2020-03",31.01],["2020-04",15.18],["2020-05",18.02],["2020-06",33.81],
    ["2020-07",37.44],["2020-08",39.37],["2020-09",36.82],["2020-10",36.39],["2020-11",38.25],["2020-12",43.92],
    // 2021
    ["2021-01",49.47],["2021-02",56.44],["2021-03",60.43],["2021-04",59.87],["2021-05",62.80],["2021-06",68.58],
    ["2021-07",70.12],["2021-08",65.68],["2021-09",69.09],["2021-10",78.51],["2021-11",76.45],["2021-12",70.56],
    // 2022
    ["2022-01",80.33],["2022-02",89.41],["2022-03",107.07],["2022-04",103.34],["2022-05",108.29],["2022-06",113.77],
    ["2022-07",100.84],["2022-08",93.76],["2022-09",84.62],["2022-10",86.61],["2022-11",84.43],["2022-12",76.45],
    // 2023
    ["2023-01",75.71],["2023-02",74.32],["2023-03",72.09],["2023-04",77.23],["2023-05",70.14],["2023-06",68.59],
    ["2023-07",74.07],["2023-08",79.78],["2023-09",87.96],["2023-10",84.65],["2023-11",77.46],["2023-12",71.01],
    // 2024
    ["2024-01",72.30],["2024-02",75.02],["2024-03",79.04],["2024-04",83.21],["2024-05",78.21],["2024-06",77.38],
    ["2024-07",79.11],["2024-08",75.00],["2024-09",68.75],["2024-10",70.45],["2024-11",68.24],["2024-12",68.10],
    // 2025
    ["2025-01",73.15],["2025-02",70.10],["2025-03",67.07],["2025-04",62.01],["2025-05",59.91],["2025-06",65.33],
    ["2025-07",65.98],["2025-08",63.37],["2025-09",62.23],["2025-10",58.89],["2025-11",58.09],["2025-12",56.26]
  ];

  const data = rawData.map(function (d) {
    var parts = d[0].split("-");
    return {
      date: new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, 1),
      price: d[1]
    };
  });

  // ========================================
  // Annotated events
  // ========================================
  const events = [
    {
      date: "1979-01",
      title: "Iranian Revolution",
      desc: "The overthrow of Shah Pahlavi disrupted Iranian oil exports, removing ~5 million barrels/day from the market and triggering panic buying worldwide.",
      side: "top"
    },
    {
      date: "1980-09",
      title: "Iran–Iraq War Begins",
      desc: "Iraq invaded Iran in September 1980, knocking out major export facilities in both countries and pushing prices to new highs above $35/barrel.",
      side: "top"
    },
    {
      date: "1986-04",
      title: "OPEC Price War / Oil Glut",
      desc: "Saudi Arabia abandoned production quotas and flooded the market to reclaim market share. Prices crashed from $27 to under $10 in months — the sharpest collapse in oil history.",
      side: "bottom"
    },
    {
      date: "1990-08",
      title: "Iraq Invades Kuwait",
      desc: "Saddam Hussein's invasion of Kuwait removed 4.3 million barrels/day from the market overnight, causing prices to spike from $17 to $41 within weeks.",
      side: "top"
    },
    {
      date: "1991-01",
      title: "Gulf War — Operation Desert Storm",
      desc: "The U.S.-led coalition launched air strikes on January 16. Oil prices initially spiked but then collapsed as the swift victory calmed market fears.",
      side: "bottom"
    },
    {
      date: "1997-11",
      title: "Asian Financial Crisis",
      desc: "Economic collapse across Southeast Asia slashed oil demand. Combined with OPEC overproduction, prices fell to inflation-adjusted all-time lows below $10/barrel.",
      side: "bottom"
    },
    {
      date: "2001-09",
      title: "September 11 Attacks",
      desc: "The 9/11 terrorist attacks caused immediate economic disruption and a sharp decline in air travel and transportation fuel demand, pushing prices down.",
      side: "top"
    },
    {
      date: "2003-03",
      title: "U.S. Invasion of Iraq",
      desc: "The Iraq War disrupted the world's fifth-largest oil exporter, compounding supply fears and marking the start of a multi-year price rally.",
      side: "top"
    },
    {
      date: "2005-08",
      title: "Hurricane Katrina",
      desc: "Katrina devastated Gulf of Mexico production infrastructure, shutting down 95% of offshore oil output and 30% of U.S. refining capacity.",
      side: "top"
    },
    {
      date: "2008-07",
      title: "All-Time High — $128/barrel",
      desc: "Surging demand from China and India, speculative trading, and geopolitical tension drove oil to a record $128/barrel before the financial crisis hit.",
      side: "top"
    },
    {
      date: "2008-12",
      title: "Global Financial Crisis",
      desc: "The collapse of Lehman Brothers triggered a worldwide recession. Oil crashed 77% in just 6 months — from $128 to $37 — the fastest decline ever recorded.",
      side: "bottom"
    },
    {
      date: "2011-02",
      title: "Arab Spring",
      desc: "Revolutions swept across the Middle East and North Africa. Libya's civil war alone removed 1.6 million barrels/day, pushing prices back above $100.",
      side: "top"
    },
    {
      date: "2014-11",
      title: "OPEC Refuses to Cut",
      desc: "Facing the U.S. shale boom, OPEC chose to defend market share over price. The decision triggered a 2-year price war that halved oil prices.",
      side: "top"
    },
    {
      date: "2016-02",
      title: "Oil Hits 13-Year Low",
      desc: "A global supply glut, slowing Chinese growth, and the U.S. shale revolution pushed oil to $26/barrel — the lowest since 2003.",
      side: "bottom"
    },
    {
      date: "2020-04",
      title: "COVID-19 Demand Collapse",
      desc: "Global lockdowns obliterated oil demand. WTI futures briefly went negative (-$37) on April 20 — an unprecedented event in oil market history.",
      side: "bottom"
    },
    {
      date: "2022-03",
      title: "Russia Invades Ukraine",
      desc: "Russia's invasion triggered Western sanctions and supply disruptions. Oil surged past $107 as Europe scrambled to replace Russian crude — the highest since 2008.",
      side: "top"
    }
  ].map(function (e) {
    var parts = e.date.split("-");
    return {
      date: new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, 1),
      title: e.title,
      desc: e.desc,
      side: e.side
    };
  });

  // ========================================
  // Chart setup
  // ========================================
  var container = document.getElementById("chart-container");
  var tooltip = document.getElementById("tooltip");
  var eventTooltip = document.getElementById("event-tooltip");

  var isSmall = container.clientWidth < 500;
  var margin = isSmall
    ? { top: 56, right: 12, bottom: 36, left: 44 }
    : { top: 60, right: 32, bottom: 40, left: 56 };

  function getSize() {
    var w = container.clientWidth;
    var h = container.clientHeight;
    return {
      width: w,
      height: h,
      innerWidth: w - margin.left - margin.right,
      innerHeight: h - margin.top - margin.bottom
    };
  }

  var size = getSize();

  var svg = d3.select(container)
    .append("svg")
    .attr("width", size.width)
    .attr("height", size.height);

  var g = svg.append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

  // Scales
  var x = d3.scaleTime()
    .domain(d3.extent(data, function (d) { return d.date; }))
    .range([0, size.innerWidth]);

  var y = d3.scaleLinear()
    .domain([0, d3.max(data, function (d) { return d.price; }) * 1.1])
    .range([size.innerHeight, 0]);

  // Area
  var area = d3.area()
    .x(function (d) { return x(d.date); })
    .y0(size.innerHeight)
    .y1(function (d) { return y(d.price); })
    .curve(d3.curveMonotoneX);

  // Line
  var line = d3.line()
    .x(function (d) { return x(d.date); })
    .y(function (d) { return y(d.price); })
    .curve(d3.curveMonotoneX);

  // ========================================
  // Draw chart
  // ========================================

  // Gradient
  var defs = svg.append("defs");
  var gradient = defs.append("linearGradient")
    .attr("id", "area-gradient")
    .attr("x1", "0").attr("y1", "0")
    .attr("x2", "0").attr("y2", "1");
  gradient.append("stop").attr("offset", "0%").attr("stop-color", "#d29922").attr("stop-opacity", 0.25);
  gradient.append("stop").attr("offset", "100%").attr("stop-color", "#d29922").attr("stop-opacity", 0.02);

  // Y axis
  var yAxisG = g.append("g")
    .attr("class", "y-axis")
    .call(
      d3.axisLeft(y)
        .ticks(6)
        .tickSize(-size.innerWidth)
        .tickFormat(function (d) { return "$" + d; })
    );
  yAxisG.select(".domain").remove();

  // X axis
  var xTickInterval = size.innerWidth < 500 ? 10 : 5;
  var xAxisG = g.append("g")
    .attr("class", "x-axis")
    .attr("transform", "translate(0," + size.innerHeight + ")")
    .call(
      d3.axisBottom(x)
        .ticks(d3.timeYear.every(xTickInterval))
        .tickFormat(d3.timeFormat(size.innerWidth < 500 ? "'%y" : "%Y"))
        .tickSize(0)
        .tickPadding(10)
    );
  xAxisG.select(".domain").attr("stroke", "var(--color-border)");

  // Area fill
  g.append("path")
    .datum(data)
    .attr("class", "price-area")
    .attr("d", area)
    .style("fill", "url(#area-gradient)");

  // Price line
  g.append("path")
    .datum(data)
    .attr("class", "price-line")
    .attr("d", line);

  // Title
  svg.append("text")
    .attr("class", "chart-title")
    .attr("x", margin.left)
    .attr("y", 28)
    .attr("font-size", "clamp(16px, 2vw, 22px)")
    .text("Crude Oil Prices — 50 Years");

  var subtitleText = size.innerWidth < 500
    ? "Monthly · 1975–2025 · Source: EIA"
    : "U.S. Crude Oil First Purchase Price ($/barrel) · Monthly · 1975–2025 · Source: EIA";
  svg.append("text")
    .attr("class", "chart-subtitle")
    .attr("x", margin.left)
    .attr("y", 46)
    .attr("font-size", "clamp(10px, 1.2vw, 13px)")
    .text(subtitleText);

  // Y axis label
  svg.append("text")
    .attr("class", "chart-subtitle")
    .attr("transform", "rotate(-90)")
    .attr("x", -(size.height / 2))
    .attr("y", 14)
    .attr("text-anchor", "middle")
    .attr("font-size", "11px")
    .text("Price ($/barrel)");

  // ========================================
  // Crosshair + price tooltip (render BEFORE events so events are on top)
  // ========================================
  var crosshairLine = g.append("line")
    .attr("class", "crosshair-line")
    .attr("y1", 0)
    .attr("y2", size.innerHeight)
    .style("display", "none");

  var crosshairDot = g.append("circle")
    .attr("class", "crosshair-dot")
    .attr("r", 5)
    .style("display", "none");

  var bisect = d3.bisector(function (d) { return d.date; }).left;

  var overlay = g.append("rect")
    .attr("class", "hover-overlay")
    .attr("width", size.innerWidth)
    .attr("height", size.innerHeight)
    .attr("fill", "none")
    .attr("pointer-events", "all")
    .style("cursor", "crosshair");

  overlay.on("mousemove", function (mouseEvt) {
    var coords = d3.pointer(mouseEvt, this);
    var mx = coords[0];
    var dateAtMouse = x.invert(mx);
    var i = bisect(data, dateAtMouse, 1);
    var d0 = data[i - 1];
    var d1 = data[i];
    if (!d0 || !d1) return;
    var d = (dateAtMouse - d0.date > d1.date - dateAtMouse) ? d1 : d0;

    var cx = x(d.date);
    var cy = y(d.price);

    crosshairLine.attr("x1", cx).attr("x2", cx).style("display", null);
    crosshairDot.attr("cx", cx).attr("cy", cy).style("display", null);

    // Tooltip
    tooltip.innerHTML =
      '<div class="tooltip-date">' + d3.timeFormat("%B %Y")(d.date) + '</div>' +
      '<div class="tooltip-price">$' + d.price.toFixed(2) + '/bbl</div>';
    tooltip.style.display = "block";

    var ttLeft = cx + margin.left + 14;
    var ttTop = cy + margin.top - 28;
    var ttWidth = tooltip.offsetWidth;

    if (ttLeft + ttWidth > size.width - 12) {
      ttLeft = cx + margin.left - ttWidth - 14;
    }
    if (ttTop < 4) { ttTop = 4; }

    tooltip.style.left = ttLeft + "px";
    tooltip.style.top = ttTop + "px";
  });

  overlay.on("mouseleave", function () {
    crosshairLine.style("display", "none");
    crosshairDot.style("display", "none");
    tooltip.style.display = "none";
  });

  // ========================================
  // Event annotations (rendered AFTER overlay so they receive mouse events)
  // ========================================
  var eventsG = g.append("g").attr("class", "events-layer");

  events.forEach(function (evt) {
    var ex = x(evt.date);
    var closest = data.reduce(function (prev, curr) {
      return Math.abs(curr.date - evt.date) < Math.abs(prev.date - evt.date) ? curr : prev;
    });
    var ey = y(closest.price);

    var markerY = evt.side === "top" ? Math.max(ey - 32, 4) : Math.min(ey + 32, size.innerHeight - 4);

    // Dashed line from marker to price line
    eventsG.append("line")
      .attr("class", "event-line")
      .attr("x1", ex).attr("y1", markerY)
      .attr("x2", ex).attr("y2", ey);

    var eventG = eventsG.append("g")
      .attr("class", "event-marker")
      .attr("transform", "translate(" + ex + "," + markerY + ")");

    // Pulse ring
    eventG.append("circle")
      .attr("class", "event-marker-pulse")
      .attr("r", 5);

    // Visible dot
    eventG.append("circle")
      .attr("class", "event-marker-circle")
      .attr("r", 5);

    // Invisible larger hit area for easier hovering
    eventG.append("circle")
      .attr("r", 14)
      .attr("fill", "transparent")
      .attr("cursor", "pointer");

    // Mouse events
    eventG.on("mouseenter", function () {
      // Hide the price crosshair while showing event tooltip
      crosshairLine.style("display", "none");
      crosshairDot.style("display", "none");
      tooltip.style.display = "none";

      var px = ex + margin.left;
      var py = markerY + margin.top;

      var ttLeft = px + 16;
      var ttTop = py - 20;

      // Position tooltip
      eventTooltip.innerHTML =
        '<div class="event-tooltip-date">' + d3.timeFormat("%B %Y")(evt.date) + '</div>' +
        '<div class="event-tooltip-title">' + evt.title + '</div>' +
        '<div class="event-tooltip-desc">' + evt.desc + '</div>';
      eventTooltip.style.display = "block";

      // Adjust if overflow right
      var ttWidth = eventTooltip.offsetWidth;
      if (ttLeft + ttWidth > size.width - 16) {
        ttLeft = px - ttWidth - 16;
      }
      // Adjust if overflow bottom
      var ttHeight = eventTooltip.offsetHeight;
      if (ttTop + ttHeight > size.height) {
        ttTop = py - ttHeight + 10;
      }
      if (ttTop < 0) {
        ttTop = 8;
      }

      eventTooltip.style.left = ttLeft + "px";
      eventTooltip.style.top = ttTop + "px";
    });

    eventG.on("mouseleave", function () {
      eventTooltip.style.display = "none";
    });
  });

  // ========================================
  // Resize handler
  // ========================================
  var resizeTimer;
  window.addEventListener("resize", function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function () {
      // Full redraw on resize
      svg.remove();
      container.querySelectorAll("svg").forEach(function (el) { el.remove(); });
      tooltip.style.display = "none";
      eventTooltip.style.display = "none";

      // Re-run by reloading (simple approach for static page)
      location.reload();
    }, 300);
  });
})();
