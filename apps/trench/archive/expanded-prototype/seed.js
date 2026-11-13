export const sourceInfo = {"file": "Копия Таблица грунтов (разработка траншеи).xlsx", "sheet": "ВР-37 ТКР10.1"};
export const seedProjects = [
  {
    "id": "excel-2",
    "name": "Д1 - КГ",
    "source": {
      "file": "Копия Таблица грунтов (разработка траншеи).xlsx",
      "sheet": "ВР-37 ТКР10.1",
      "range": "A2:I26"
    },
    "materials": [
      {
        "name": "Подушка из ЩПС h=0,15м",
        "volume": 18.788,
        "cell": "D8",
        "formula": null,
        "original": 18.788
      },
      {
        "name": "Засыпка из ЩПС",
        "volume": 86.821,
        "cell": "D9",
        "formula": null,
        "original": 86.821
      },
      {
        "name": "Защитный слой из ЩПС h=0,3м",
        "volume": 93.963,
        "cell": "D10",
        "formula": null,
        "original": 93.963
      },
      {
        "name": "Засыпка траншеи ЩПС",
        "volume": 316.449,
        "cell": "D11",
        "formula": null,
        "original": 316.449
      }
    ],
    "pipes": [
      {
        "name": "Футляр ПЭ100 SDR17 Ду=630мм l=11,43м",
        "length": 11.43,
        "area": 0.312,
        "diameter": 630.0,
        "method": "area",
        "count": 1,
        "cell": "D17",
        "formula": "11.43*0.312",
        "original": 3.56616
      },
      {
        "name": "Футляр ПЭ100 SDR17 Ду=500мм l=109,15м",
        "length": 109.15,
        "area": 0.196,
        "diameter": 500.0,
        "method": "area",
        "count": 1,
        "cell": "D18",
        "formula": "109.15*0.196",
        "original": 21.393400000000003
      }
    ],
    "structures": [
      {
        "name": "Дождеприемный колодец Д1",
        "volume": 9.366,
        "excavation": 12.26946,
        "cell": "D21",
        "formula": null,
        "original": 9.366,
        "excavationSource": {
          "cell": "D22",
          "formula": "(D21*131%)",
          "original": 12.26946
        },
        "soilNote": "ИГЭ-3а (II гр.) - 100%"
      },
      {
        "name": "Канализационная насосная станция-2",
        "volume": 29.428,
        "excavation": 43.25916,
        "cell": "D23",
        "formula": null,
        "original": 29.428,
        "excavationSource": {
          "cell": "D24",
          "formula": "D23*147%",
          "original": 43.25916
        },
        "soilNote": "ИГЭ-3а (II гр.) - 100%"
      }
    ],
    "groups": [
      11.9,
      67.0,
      21.1,
      0
    ],
    "notes": [
      {
        "label": "грунты I группы",
        "cell": "D5",
        "formula": "(D3*11.9%)",
        "original": 76.119659
      },
      {
        "label": "грунты II группы",
        "cell": "D6",
        "formula": "(D3*67%)",
        "original": 428.57286999999997
      },
      {
        "label": "грунты III группы",
        "cell": "D7",
        "formula": "(D3*21.1%)",
        "original": 134.968471
      }
    ],
    "sourceWarnings": [],
    "totalExcavation": 639.661,
    "soilNote": "Распределение выемки по грунтам: ИГЭ-1 (III гр.) - 13,5%; ИГЭ-3а (II гр.) - 37,2%; ИГЭ-4 (III гр.) - 7,6%; ИГЭ-5 (I гр.) - 11,9%; ИГЭ-6б (II гр.) - 29,8%",
    "totalSource": {
      "cell": "D3",
      "formula": null,
      "original": 639.661
    },
    "originalBackfill": 43.15181999999999,
    "backfillSource": {
      "cell": "D25",
      "formula": "D3-D12-D26",
      "original": 43.15181999999999
    },
    "originalPitBackfill": 16.734620000000007,
    "pitBackfillSource": {
      "cell": "D26",
      "formula": "(D22+D24)-(D21+D23)",
      "original": 16.734620000000007
    }
  },
  {
    "id": "excel-27",
    "name": "ККл-1 - КК2-35",
    "source": {
      "file": "Копия Таблица грунтов (разработка траншеи).xlsx",
      "sheet": "ВР-37 ТКР10.1",
      "range": "A27:I65"
    },
    "materials": [
      {
        "name": "Подушка из ЩПС h=0,15м",
        "volume": 70.563,
        "cell": "D33",
        "formula": null,
        "original": 70.563
      },
      {
        "name": "Засыпка из ЩПС",
        "volume": 713.097,
        "cell": "D34",
        "formula": null,
        "original": 713.097
      },
      {
        "name": "Защитный слой из ЩПС h=0,3м",
        "volume": 359.758,
        "cell": "D35",
        "formula": null,
        "original": 359.758
      },
      {
        "name": "Засыпка траншеи ЩПС",
        "volume": 4132.461,
        "cell": "D36",
        "formula": null,
        "original": 4132.461
      }
    ],
    "pipes": [
      {
        "name": "Труба КОРСИС ПРО SN16 Ду=1200мм l=227,33м",
        "length": 227.33,
        "area": 1.131,
        "diameter": 1200.0,
        "method": "area",
        "count": 1,
        "cell": "D42",
        "formula": "227.33*1.131",
        "original": 257.11023
      },
      {
        "name": "Труба СПИРОЛАЙН Т1.П SN16 Ду=1840мм l=22,16м",
        "length": 22.16,
        "area": 2.658,
        "diameter": 1840.0,
        "method": "area",
        "count": 1,
        "cell": "D43",
        "formula": "22.16*2.658",
        "original": 58.90128
      }
    ],
    "structures": [
      {
        "name": "Переустраиваемый колодец ККл-1",
        "volume": 48.939,
        "excavation": 70.96155,
        "cell": "D46",
        "formula": null,
        "original": 48.939,
        "excavationSource": {
          "cell": "D47",
          "formula": "(D46*145%)",
          "original": 70.96155
        },
        "soilNote": "ИГЭ-3б (II гр.) - 45,1%; ИГЭ-5б (I гр.) - 54,9%;"
      },
      {
        "name": "Перепадная камера КК2-23",
        "volume": 71.156,
        "excavation": 192.12120000000002,
        "cell": "D48",
        "formula": null,
        "original": 71.156,
        "excavationSource": {
          "cell": "D49",
          "formula": "(D48*270%)",
          "original": 192.12120000000002
        },
        "soilNote": "ИГЭ-3б (II гр.) - 41,4%; ИГЭ-5б (I гр.) - 58,6%;"
      },
      {
        "name": "Перепадная камера КК2-24",
        "volume": 75.457,
        "excavation": 208.26131999999996,
        "cell": "D50",
        "formula": null,
        "original": 75.457,
        "excavationSource": {
          "cell": "D51",
          "formula": "(D50*276%)",
          "original": 208.26131999999996
        },
        "soilNote": "ИГЭ-3б (II гр.) - 29,4%; ИГЭ-5б (I гр.) - 70,6%;"
      },
      {
        "name": "Перепадная камера КК2-25",
        "volume": 79.449,
        "excavation": 190.67759999999998,
        "cell": "D52",
        "formula": null,
        "original": 79.449,
        "excavationSource": {
          "cell": "D53",
          "formula": "(D52*240%)",
          "original": 190.67759999999998
        },
        "soilNote": "ИГЭ-3б (II гр.) - 49,3%; ИГЭ-5 (I гр.) - 50,7%;"
      },
      {
        "name": "Перепадная камера КК2-26",
        "volume": 73.614,
        "excavation": 200.96622000000002,
        "cell": "D54",
        "formula": null,
        "original": 73.614,
        "excavationSource": {
          "cell": "D55",
          "formula": "(D54*273%)",
          "original": 200.96622000000002
        },
        "soilNote": "ИГЭ-3б (II гр.) - 67,4%; ИГЭ-5 (I гр.) - 6,1%; ИГЭ-7а - 26,5%"
      },
      {
        "name": "Линейный колодец КК2-27",
        "volume": 59.792,
        "excavation": 89.688,
        "cell": "D56",
        "formula": null,
        "original": 59.792,
        "excavationSource": {
          "cell": "D57",
          "formula": "(D56*150%)",
          "original": 89.688
        },
        "soilNote": "ИГЭ-1 (III гр.) - 78,2%; ИГЭ-5 (I гр.) - 21,8%;"
      },
      {
        "name": "Поворотный колодец КК2-33",
        "volume": 33.479,
        "excavation": 41.848749999999995,
        "cell": "D58",
        "formula": null,
        "original": 33.479,
        "excavationSource": {
          "cell": "D59",
          "formula": "(D58*125%)",
          "original": 41.848749999999995
        },
        "soilNote": "ИГЭ-1а (IV гр.) - 100%"
      },
      {
        "name": "Приемный колодец КК2-34",
        "volume": 33.07,
        "excavation": 40.3454,
        "cell": "D60",
        "formula": null,
        "original": 33.07,
        "excavationSource": {
          "cell": "D61",
          "formula": "(D60*122%)",
          "original": 40.3454
        },
        "soilNote": "ИГЭ-1а (IV гр.) - 100%"
      },
      {
        "name": "Приемный колодец КК2-35",
        "volume": 33.07,
        "excavation": 40.3454,
        "cell": "D62",
        "formula": null,
        "original": 33.07,
        "excavationSource": {
          "cell": "D63",
          "formula": "(D62*122%)",
          "original": 40.3454
        },
        "soilNote": "ИГЭ-1а (IV гр.) - 100%"
      }
    ],
    "groups": [
      36.7,
      51.8,
      11.5,
      0
    ],
    "notes": [
      {
        "label": "грунты I группы",
        "cell": "D30",
        "formula": "(D28*36.7%)",
        "original": 2874.5906240000004
      },
      {
        "label": "грунты II группы",
        "cell": "D31",
        "formula": "(D28*51.8%)",
        "original": 4057.324096
      },
      {
        "label": "грунты III группы",
        "cell": "D32",
        "formula": "(D28*11.5%)",
        "original": 900.75728
      }
    ],
    "sourceWarnings": [],
    "totalExcavation": 7832.672,
    "soilNote": "Распределение выемки по грунтам: ИГЭ-3б (II гр.) - 43,8%; ИГЭ-5б (I гр.) - 27,3%; ИГЭ-5 (I гр.) - 9,4%; ИГЭ-4 (III гр.) - 2,1%; ИГЭ-1 (III гр.) - 9,4%; ИГЭ-7а (II гр.) - 8%",
    "totalSource": {
      "cell": "D28",
      "formula": null,
      "original": 7832.672
    },
    "originalBackfill": 1165.5660499999997,
    "backfillSource": {
      "cell": "D64",
      "formula": "D28-D37-D65",
      "original": 1165.5660499999997
    },
    "originalPitBackfill": 567.1894399999999,
    "pitBackfillSource": {
      "cell": "D65",
      "formula": "(D47+D49+D51+D53+D55+D57+D59+D61+D63)-(D46+D48+D50+D52+D54+D56+D58+D60+D62)",
      "original": 567.1894399999999
    }
  },
  {
    "id": "excel-66",
    "name": "КНС - КК2-34",
    "source": {
      "file": "Копия Таблица грунтов (разработка траншеи).xlsx",
      "sheet": "ВР-37 ТКР10.1",
      "range": "A66:I89"
    },
    "materials": [
      {
        "name": "Подушка из ЩПС h=0,15м",
        "volume": 3.605,
        "cell": "D72",
        "formula": null,
        "original": 3.605
      },
      {
        "name": "Засыпка из ЩПС",
        "volume": 160.76,
        "cell": "D73",
        "formula": null,
        "original": 160.76
      },
      {
        "name": "Защитный слой из ЩПС h=0,3м",
        "volume": 111.883,
        "cell": "D74",
        "formula": null,
        "original": 111.883
      }
    ],
    "pipes": [
      {
        "name": "Труба из стали 17Г1С Ду=1020мм l=147,01м",
        "length": 147.01,
        "area": 0.785,
        "diameter": 1020.0,
        "method": "area",
        "count": 1,
        "cell": "D80",
        "formula": "147.01*0.785",
        "original": 115.40285
      },
      {
        "name": "Труба КОРСИС ПРО SN16 Ду=1200мм l=3,97м",
        "length": 3.97,
        "area": 1.131,
        "diameter": 1200.0,
        "method": "area",
        "count": 1,
        "cell": "D81",
        "formula": "3.97*1.131",
        "original": 4.49007
      }
    ],
    "structures": [
      {
        "name": "Колодец-гаситель",
        "volume": 35.05,
        "excavation": 43.461999999999996,
        "cell": "D84",
        "formula": null,
        "original": 35.05,
        "excavationSource": {
          "cell": "D85",
          "formula": "D84*124%",
          "original": 43.461999999999996
        },
        "soilNote": "ИГЭ-1а (IV гр.) - 100%"
      },
      {
        "name": "Приемный колодец КК2-34",
        "volume": 33.07,
        "excavation": 40.3454,
        "cell": "D86",
        "formula": null,
        "original": 33.07,
        "excavationSource": {
          "cell": "D87",
          "formula": "D86*122%",
          "original": 40.3454
        },
        "soilNote": "ИГЭ-1а (IV гр.) - 100%"
      }
    ],
    "groups": [
      0,
      26.7,
      45.9,
      27.4
    ],
    "notes": [
      {
        "label": "грунты II группы",
        "cell": "D69",
        "formula": "(D67*26.7%)",
        "original": 409.634604
      },
      {
        "label": "грунты III группы",
        "cell": "D70",
        "formula": "(D67*45.9%)",
        "original": 704.203308
      },
      {
        "label": "грунты IV группы",
        "cell": "D71",
        "formula": "(D67*27.4%)",
        "original": 420.374088
      }
    ],
    "sourceWarnings": [],
    "totalExcavation": 1534.212,
    "soilNote": "Распределение выемки по грунтам: ИГЭ-1б (II гр.) - 26,7%; ИГЭ-1а (IV гр.) - 27,4%; ИГЭ-1 (III гр.) - 45,9%",
    "totalSource": {
      "cell": "D67",
      "formula": null,
      "original": 1534.212
    },
    "originalBackfill": 1054.26368,
    "backfillSource": {
      "cell": "D88",
      "formula": "D67-D75-D89",
      "original": 1054.26368
    },
    "originalPitBackfill": 15.687399999999997,
    "pitBackfillSource": {
      "cell": "D89",
      "formula": "(D85+D87)-(D84+D86)",
      "original": 15.687399999999997
    }
  },
  {
    "id": "excel-90",
    "name": "КДр-1 - КК2-34",
    "source": {
      "file": "Копия Таблица грунтов (разработка траншеи).xlsx",
      "sheet": "ВР-37 ТКР10.1",
      "range": "A90:I125"
    },
    "materials": [
      {
        "name": "Подушка из ЩПС h=0,15м",
        "volume": 23.23,
        "cell": "D94",
        "formula": null,
        "original": 23.23
      },
      {
        "name": "Засыпка из ЩПС",
        "volume": 136.597,
        "cell": "D95",
        "formula": null,
        "original": 136.597
      },
      {
        "name": "Защитный слой из ЩПС h=0,3м",
        "volume": 110.151,
        "cell": "D96",
        "formula": null,
        "original": 110.151
      },
      {
        "name": "Засыпка траншеи ЩПС",
        "volume": 672.314,
        "cell": "D97",
        "formula": null,
        "original": 672.314
      }
    ],
    "pipes": [
      {
        "name": "Труба КОРСИС ПРО SN16 Ду=400мм l=7,52м",
        "length": 7.52,
        "area": 0.126,
        "diameter": 400.0,
        "method": "area",
        "count": 1,
        "cell": "D103",
        "formula": "7.52*0.126",
        "original": 0.9475199999999999
      },
      {
        "name": "Труба КОРСИС ПРО SN16 Ду=500мм l=40,91м",
        "length": 40.91,
        "area": 0.196,
        "diameter": 500.0,
        "method": "area",
        "count": 1,
        "cell": "D104",
        "formula": "40.91*0.196",
        "original": 8.01836
      },
      {
        "name": "Футляр ПЭ100 SDR17 Ду=710мм l=6,27м",
        "length": 6.27,
        "area": 0.396,
        "diameter": 710.0,
        "method": "area",
        "count": 1,
        "cell": "D105",
        "formula": "6.27*0.396",
        "original": 2.48292
      },
      {
        "name": "Футляр ПЭ100 SDR17 Ду=800мм l=72,56м",
        "length": 72.56,
        "area": 0.503,
        "diameter": 800.0,
        "method": "area",
        "count": 1,
        "cell": "D106",
        "formula": "72.56*0.503",
        "original": 36.49768
      },
      {
        "name": "Труба КОРСИС ПРО SN16 Ду=1200мм l=3,73м",
        "length": 3.73,
        "area": 1.131,
        "diameter": 1200.0,
        "method": "area",
        "count": 1,
        "cell": "D107",
        "formula": "3.73*1.131",
        "original": 4.21863
      }
    ],
    "structures": [
      {
        "name": "Поворотный колодец КК2-28",
        "volume": 10.026,
        "excavation": 12.0312,
        "cell": "D110",
        "formula": null,
        "original": 10.026,
        "excavationSource": {
          "cell": "D111",
          "formula": "D110*120%",
          "original": 12.0312
        },
        "soilNote": "ИГЭ-1а (IV гр.) - 100%"
      },
      {
        "name": "Перепадной колодец КК2-35",
        "volume": 14.53,
        "excavation": 19.470200000000002,
        "cell": "D112",
        "formula": null,
        "original": 14.53,
        "excavationSource": {
          "cell": "D113",
          "formula": "D112*134%",
          "original": 19.470200000000002
        },
        "soilNote": "ИГЭ-1а (IV гр.) - 100%"
      },
      {
        "name": "Поворотный колодец КК2-29",
        "volume": 13.126,
        "excavation": 14.701120000000001,
        "cell": "D114",
        "formula": null,
        "original": 13.126,
        "excavationSource": {
          "cell": "D115",
          "formula": "D114*112%",
          "original": 14.701120000000001
        },
        "soilNote": "ИГЭ-1а (IV гр.) - 50%; ИГЭ-1б (II гр.) - 50%"
      },
      {
        "name": "Дренажный колодец Дт4",
        "volume": 7.265,
        "excavation": 8.427399999999999,
        "cell": "D116",
        "formula": null,
        "original": 7.265,
        "excavationSource": {
          "cell": "D117",
          "formula": "D116*116%",
          "original": 8.427399999999999
        },
        "soilNote": "ИГЭ-1а (IV гр.) - 100%"
      },
      {
        "name": "Поворотный колодец КК2-30",
        "volume": 14.046,
        "excavation": 16.433819999999997,
        "cell": "D118",
        "formula": null,
        "original": 14.046,
        "excavationSource": {
          "cell": "D119",
          "formula": "D118*117%",
          "original": 16.433819999999997
        },
        "soilNote": "ИГЭ-1 (III гр.) - 50%; ИГЭ-1а (IV гр.) - 50%"
      },
      {
        "name": "Поворотный колодец КК2-33",
        "volume": 33.479,
        "excavation": 41.848749999999995,
        "cell": "D120",
        "formula": null,
        "original": 33.479,
        "excavationSource": {
          "cell": "D121",
          "formula": "D120*125%",
          "original": 41.848749999999995
        },
        "soilNote": "ИГЭ-1а (IV гр.) - 100%"
      },
      {
        "name": "Приемный колодец КК2-34",
        "volume": 33.07,
        "excavation": 40.3454,
        "cell": "D122",
        "formula": null,
        "original": 33.07,
        "excavationSource": {
          "cell": "D123",
          "formula": "D122*122%",
          "original": 40.3454
        },
        "soilNote": "ИГЭ-1а (IV гр.) - 100%"
      }
    ],
    "groups": [
      0,
      0,
      0,
      100.0
    ],
    "notes": [
      {
        "label": "грунты IV группы",
        "cell": "D93",
        "formula": "(D91*100%)",
        "original": 1214.208
      }
    ],
    "sourceWarnings": [
      "Боковая колонка I92: 1069.37751 м³, по подробным строкам 1060.95011 м³ (выемка под траншею). В системе используется сумма подробных строк, а не боковой итог.",
      "Боковая колонка I94: 74.92040 м³, по подробным строкам 66.49300 м³ (обратная засыпка траншеи). В системе используется сумма подробных строк, а не боковой итог."
    ],
    "totalExcavation": 1214.208,
    "soilNote": "Распределение выемки по грунтам: ИГЭ-1а (IV гр.) - 100%",
    "totalSource": {
      "cell": "D91",
      "formula": null,
      "original": 1214.208
    },
    "originalBackfill": 66.49300000000014,
    "backfillSource": {
      "cell": "D124",
      "formula": "D91-D98-D125",
      "original": 66.49300000000014
    },
    "originalPitBackfill": 27.715889999999973,
    "pitBackfillSource": {
      "cell": "D125",
      "formula": "(D111+D113+D115+D117+D119+D121+D123)-(D110+D112+D114+D116+D118+D120+D122)",
      "original": 27.715889999999973
    }
  },
  {
    "id": "excel-126",
    "name": "Д14 - КНС",
    "source": {
      "file": "Копия Таблица грунтов (разработка траншеи).xlsx",
      "sheet": "ВР-37 ТКР10.1",
      "range": "A126:I158"
    },
    "materials": [
      {
        "name": "Подушка из ЩПС h=0,15м",
        "volume": 14.049,
        "cell": "D132",
        "formula": null,
        "original": 14.049
      },
      {
        "name": "Засыпка из ЩПС",
        "volume": 77.409,
        "cell": "D133",
        "formula": null,
        "original": 77.409
      },
      {
        "name": "Защитный слой из ЩПС h=0,3м",
        "volume": 65.829,
        "cell": "D134",
        "formula": null,
        "original": 65.829
      },
      {
        "name": "Засыпка траншеи ЩПС",
        "volume": 258.112,
        "cell": "D135",
        "formula": null,
        "original": 258.112
      }
    ],
    "pipes": [
      {
        "name": "Труба КОРСИС ПРО SN16 Ду=400мм l=27,14м",
        "length": 27.14,
        "area": 0.126,
        "diameter": 400.0,
        "method": "area",
        "count": 1,
        "cell": "D141",
        "formula": "27.14*0.126",
        "original": 3.4196400000000002
      },
      {
        "name": "Труба КОРСИС ПРО SN16 Ду=500мм l=13,21м",
        "length": 13.21,
        "area": 0.196,
        "diameter": 500.0,
        "method": "area",
        "count": 1,
        "cell": "D142",
        "formula": "13.21*0.196",
        "original": 2.58916
      },
      {
        "name": "Футляр ПЭ100 SDR17 Ду=710мм l=28,18м",
        "length": 28.18,
        "area": 0.396,
        "diameter": 710.0,
        "method": "area",
        "count": 1,
        "cell": "D143",
        "formula": "28.18*0.396",
        "original": 11.15928
      },
      {
        "name": "Труба ПЭ100 SDR17 Ду=1400мм l=5,97м",
        "length": 5.97,
        "area": 1.539,
        "diameter": 1400.0,
        "method": "area",
        "count": 1,
        "cell": "D144",
        "formula": "5.97*1.539",
        "original": 9.18783
      }
    ],
    "structures": [
      {
        "name": "Дождеприемный колодец Д14",
        "volume": 10.026,
        "excavation": 13.0338,
        "cell": "D147",
        "formula": null,
        "original": 10.026,
        "excavationSource": {
          "cell": "D148",
          "formula": "D147*130%",
          "original": 13.0338
        },
        "soilNote": "ИГЭ-1а (IV гр.) - 100%"
      },
      {
        "name": "Дождеприемный колодец Д14'",
        "volume": 14.53,
        "excavation": 19.3249,
        "cell": "D149",
        "formula": null,
        "original": 14.53,
        "excavationSource": {
          "cell": "D150",
          "formula": "D149*133%",
          "original": 19.3249
        },
        "soilNote": "ИГЭ-1а (IV гр.) - 100%"
      },
      {
        "name": "Поворотный колодец КК2-14",
        "volume": 13.126,
        "excavation": 17.45758,
        "cell": "D151",
        "formula": null,
        "original": 13.126,
        "excavationSource": {
          "cell": "D152",
          "formula": "D151*133%",
          "original": 17.45758
        },
        "soilNote": "ИГЭ-1а (IV гр.) - 100%"
      },
      {
        "name": "Поворотный колодец КК2-15",
        "volume": 7.265,
        "excavation": 9.22655,
        "cell": "D153",
        "formula": null,
        "original": 7.265,
        "excavationSource": {
          "cell": "D154",
          "formula": "D153*127%",
          "original": 9.22655
        },
        "soilNote": "ИГЭ-1а (IV гр.) - 100%"
      },
      {
        "name": "Поворотный колодец КК2-16",
        "volume": 14.046,
        "excavation": 18.40026,
        "cell": "D155",
        "formula": null,
        "original": 14.046,
        "excavationSource": {
          "cell": "D156",
          "formula": "D155*131%",
          "original": 18.40026
        },
        "soilNote": "ИГЭ-1 (III гр.) - 28,6%; ИГЭ-3г (I гр.) - 71,4%;"
      }
    ],
    "groups": [
      10.9,
      0,
      39.7,
      49.4
    ],
    "notes": [
      {
        "label": "грунты I группы",
        "cell": "D129",
        "formula": "(D127*10.9%)",
        "original": 74.580089
      },
      {
        "label": "грунты III группы",
        "cell": "D130",
        "formula": "(D127*39.7%)",
        "original": 271.635737
      },
      {
        "label": "грунты IV группы",
        "cell": "D131",
        "formula": "(D127*49.4%)",
        "original": 338.005174
      }
    ],
    "sourceWarnings": [],
    "totalExcavation": 684.221,
    "soilNote": "Распределение выемки по грунтам: ИГЭ-1 (III гр.) - 39,7%; ИГЭ-1а (IV гр.) - 49,4%; ИГЭ-3г (I гр.) - 10,9%",
    "totalSource": {
      "cell": "D127",
      "formula": null,
      "original": 684.221
    },
    "originalBackfill": 165.02300000000002,
    "backfillSource": {
      "cell": "D157",
      "formula": "D127-D136-D158",
      "original": 165.02300000000002
    },
    "originalPitBackfill": 18.450090000000003,
    "pitBackfillSource": {
      "cell": "D158",
      "formula": "(D148+D150+D152+D154+D156)-(D147+D149+D151+D153+D155)",
      "original": 18.450090000000003
    }
  },
  {
    "id": "excel-159",
    "name": "Д12 - КК2-12",
    "source": {
      "file": "Копия Таблица грунтов (разработка траншеи).xlsx",
      "sheet": "ВР-37 ТКР10.1",
      "range": "A159:I181"
    },
    "materials": [
      {
        "name": "Подушка из ЩПС h=0,15м",
        "volume": 3.244,
        "cell": "D164",
        "formula": null,
        "original": 3.244
      },
      {
        "name": "Засыпка из ЩПС",
        "volume": 18.765,
        "cell": "D165",
        "formula": null,
        "original": 18.765
      },
      {
        "name": "Защитный слой из ЩПС h=0,3м",
        "volume": 15.407,
        "cell": "D166",
        "formula": null,
        "original": 15.407
      },
      {
        "name": "Засыпка траншеи ЩПС",
        "volume": 97.388,
        "cell": "D167",
        "formula": null,
        "original": 97.388
      }
    ],
    "pipes": [
      {
        "name": "Футляр ПЭ100 SDR17 Ду=710мм l=19,19м",
        "length": 19.19,
        "area": 0.396,
        "diameter": 710.0,
        "method": "area",
        "count": 1,
        "cell": "D173",
        "formula": "19.19*0.396",
        "original": 7.599240000000001
      }
    ],
    "structures": [
      {
        "name": "Дождеприемный колодец Д12",
        "volume": 6.217,
        "excavation": 8.26861,
        "cell": "D176",
        "formula": null,
        "original": 6.217,
        "excavationSource": {
          "cell": "D177",
          "formula": "D176*133%",
          "original": 8.26861
        },
        "soilNote": "ИГЭ-1б (II гр.) - 100%"
      },
      {
        "name": "Приемный колодец КК2-12",
        "volume": 9.611,
        "excavation": 12.782630000000001,
        "cell": "D178",
        "formula": null,
        "original": 9.611,
        "excavationSource": {
          "cell": "D179",
          "formula": "D178*133%",
          "original": 12.782630000000001
        },
        "soilNote": "ИГЭ-1б (II гр.) - 47,1%; ИГЭ-3б1 - 29,4%; ИГЭ-3б - 23,5%;"
      }
    ],
    "groups": [
      0,
      42.2,
      57.8,
      0
    ],
    "notes": [
      {
        "label": "грунты II группы",
        "cell": "D162",
        "formula": "(D160*42.2%)",
        "original": 68.97758800000001
      },
      {
        "label": "грунты III группы",
        "cell": "D163",
        "formula": "(D160*57.8%)",
        "original": 94.476412
      }
    ],
    "sourceWarnings": [],
    "totalExcavation": 163.454,
    "soilNote": "Распределение выемки по грунтам: ИГЭ-1б (II гр.) - 32,9%; ИГЭ-1 (III гр.) - 44,1%; ИГЭ-3б (II гр.) - 9,3%; ИГЭ-3б1 (III гр.) - 13,7%",
    "totalSource": {
      "cell": "D160",
      "formula": null,
      "original": 163.454
    },
    "originalBackfill": -0.0004800000000066973,
    "backfillSource": {
      "cell": "D180",
      "formula": "D160-D168-D181",
      "original": -0.0004800000000066973
    },
    "originalPitBackfill": 5.2232400000000005,
    "pitBackfillSource": {
      "cell": "D181",
      "formula": "(D177+D179)-(D176+D178)",
      "original": 5.2232400000000005
    }
  },
  {
    "id": "excel-182",
    "name": "Д12' - КК2-12",
    "source": {
      "file": "Копия Таблица грунтов (разработка траншеи).xlsx",
      "sheet": "ВР-37 ТКР10.1",
      "range": "A182:I204"
    },
    "materials": [
      {
        "name": "Подушка из ЩПС h=0,15м",
        "volume": 1.74,
        "cell": "D187",
        "formula": null,
        "original": 1.74
      },
      {
        "name": "Засыпка из ЩПС",
        "volume": 10.067,
        "cell": "D188",
        "formula": null,
        "original": 10.067
      },
      {
        "name": "Защитный слой из ЩПС h=0,3м",
        "volume": 8.266,
        "cell": "D189",
        "formula": null,
        "original": 8.266
      },
      {
        "name": "Засыпка траншеи ЩПС",
        "volume": 43.802,
        "cell": "D190",
        "formula": null,
        "original": 43.802
      }
    ],
    "pipes": [
      {
        "name": "Футляр ПЭ100 SDR17 Ду=710мм l=6,98м",
        "length": 6.98,
        "area": 0.396,
        "diameter": 710.0,
        "method": "area",
        "count": 1,
        "cell": "D196",
        "formula": "6.98*0.396",
        "original": 2.7640800000000003
      }
    ],
    "structures": [
      {
        "name": "Дождеприемный колодец Д12'",
        "volume": 6.217,
        "excavation": 8.26861,
        "cell": "D199",
        "formula": null,
        "original": 6.217,
        "excavationSource": {
          "cell": "D200",
          "formula": "D199*133%",
          "original": 8.26861
        },
        "soilNote": "ИГЭ-1б (II гр.) - 100%;"
      },
      {
        "name": "Приемный колодец КК2-12",
        "volume": 9.611,
        "excavation": 12.782630000000001,
        "cell": "D201",
        "formula": null,
        "original": 9.611,
        "excavationSource": {
          "cell": "D202",
          "formula": "D201*133%",
          "original": 12.782630000000001
        },
        "soilNote": "ИГЭ-1б (II гр.) - 57,9%; ИГЭ-3б1 - 23,9%; ИГЭ-3б - 18,2%;"
      }
    ],
    "groups": [
      0,
      75.3,
      24.7,
      0
    ],
    "notes": [
      {
        "label": "грунты II группы",
        "cell": "D185",
        "formula": "(D183*75.3%)",
        "original": 66.03057
      },
      {
        "label": "грунты III группы",
        "cell": "D186",
        "formula": "(D183*24.7%)",
        "original": 21.65943
      }
    ],
    "sourceWarnings": [],
    "totalExcavation": 87.69,
    "soilNote": "Распределение выемки по грунтам: ИГЭ-1б (II гр.) - 67,7%; ИГЭ-3б (II гр.) - 7,6%; ИГЭ-3б1 (III гр.) - 24,7%",
    "totalSource": {
      "cell": "D183",
      "formula": null,
      "original": 87.69
    },
    "originalBackfill": -0.0003200000000127545,
    "backfillSource": {
      "cell": "D203",
      "formula": "D183-D191-D204",
      "original": -0.0003200000000127545
    },
    "originalPitBackfill": 5.2232400000000005,
    "pitBackfillSource": {
      "cell": "D204",
      "formula": "(D200+D202)-(D199+D201)",
      "original": 5.2232400000000005
    }
  },
  {
    "id": "excel-205",
    "name": "Д13 - КК2-13",
    "source": {
      "file": "Копия Таблица грунтов (разработка траншеи).xlsx",
      "sheet": "ВР-37 ТКР10.1",
      "range": "A205:I231"
    },
    "materials": [
      {
        "name": "Подушка из ЩПС h=0,15м",
        "volume": 7.396,
        "cell": "D211",
        "formula": null,
        "original": 7.396
      },
      {
        "name": "Засыпка из ЩПС",
        "volume": 38.058,
        "cell": "D212",
        "formula": null,
        "original": 38.058
      },
      {
        "name": "Защитный слой из ЩПС h=0,3м",
        "volume": 34.439,
        "cell": "D213",
        "formula": null,
        "original": 34.439
      },
      {
        "name": "Засыпка траншеи ЩПС",
        "volume": 189.958,
        "cell": "D214",
        "formula": null,
        "original": 189.958
      }
    ],
    "pipes": [
      {
        "name": "Труба КОРСИС ПРО SN16 Ду=400мм l=11,91м",
        "length": 11.91,
        "area": 0.126,
        "diameter": 400.0,
        "method": "area",
        "count": 1,
        "cell": "D220",
        "formula": "11.91*0.126",
        "original": 1.50066
      },
      {
        "name": "Футляр ПЭ100 SDR17 Ду=710мм l=27,06м",
        "length": 27.06,
        "area": 0.396,
        "diameter": 710.0,
        "method": "area",
        "count": 1,
        "cell": "D221",
        "formula": "27.06*0.396",
        "original": 10.71576
      }
    ],
    "structures": [
      {
        "name": "Дождеприемный колодец Д13",
        "volume": 6.782,
        "excavation": 9.02006,
        "cell": "D224",
        "formula": null,
        "original": 6.782,
        "excavationSource": {
          "cell": "D225",
          "formula": "D224*133%",
          "original": 9.02006
        },
        "soilNote": "ИГЭ-1 (III гр.) - 56,8%; ИГЭ-1а (IV гр.) - 43,2%;"
      },
      {
        "name": "Дождеприемный колодец Д13'",
        "volume": 6.886,
        "excavation": 9.158380000000001,
        "cell": "D226",
        "formula": null,
        "original": 6.886,
        "excavationSource": {
          "cell": "D227",
          "formula": "D226*133%",
          "original": 9.158380000000001
        },
        "soilNote": "ИГЭ-1а (IV гр.) - 70,1%; ИГЭ-3б1 - 16,9%; ИГЭ-3б - 13%;"
      },
      {
        "name": "Приемный колодец КК2-13",
        "volume": 9.714,
        "excavation": 12.919620000000002,
        "cell": "D228",
        "formula": null,
        "original": 9.714,
        "excavationSource": {
          "cell": "D229",
          "formula": "D228*133%",
          "original": 12.919620000000002
        },
        "soilNote": "ИГЭ-1а (IV гр.) - 30,6%; ИГЭ-3б1 - 11,2%; ИГЭ-3б - 58,2%;"
      }
    ],
    "groups": [
      0,
      6.6,
      35.5,
      58.9
    ],
    "notes": [
      {
        "label": "грунты II группы",
        "cell": "D208",
        "formula": "(D206*6.6%)",
        "original": 20.924772
      },
      {
        "label": "грунты III группы",
        "cell": "D209",
        "formula": "(D206*35.5%)",
        "original": 112.54990999999998
      },
      {
        "label": "грунты IV группы",
        "cell": "D210",
        "formula": "(D206*58.9%)",
        "original": 186.73773799999998
      }
    ],
    "sourceWarnings": [
      "Сумма долей групп в исходных строках = 101%, а не 100%. Доли не нормализованы автоматически; требуется уточнение инженера."
    ],
    "totalExcavation": 317.042,
    "soilNote": "Распределение выемки по грунтам: ИГЭ-1 (III гр.) - 21,7%; ИГЭ-1а (IV гр.) - 58,9%; ИГЭ-3б (II гр.) - 6,6%; ИГЭ-3б1 (III гр.) - 13,8%",
    "totalSource": {
      "cell": "D206",
      "formula": null,
      "original": 317.042
    },
    "originalBackfill": 3.876519999999992,
    "backfillSource": {
      "cell": "D230",
      "formula": "D206-D215-D231",
      "original": 3.876519999999992
    },
    "originalPitBackfill": 7.716060000000006,
    "pitBackfillSource": {
      "cell": "D231",
      "formula": "(D225+D227+D229)-(D224+D226+D228)",
      "original": 7.716060000000006
    }
  },
  {
    "id": "excel-232",
    "name": "Д23 - КК2-23",
    "source": {
      "file": "Копия Таблица грунтов (разработка траншеи).xlsx",
      "sheet": "ВР-37 ТКР10.1",
      "range": "A232:I259"
    },
    "materials": [
      {
        "name": "Подушка из ЩПС h=0,15м",
        "volume": 7.395,
        "cell": "D239",
        "formula": null,
        "original": 7.395
      },
      {
        "name": "Засыпка из ЩПС",
        "volume": 39.402,
        "cell": "D240",
        "formula": null,
        "original": 39.402
      },
      {
        "name": "Защитный слой из ЩПС h=0,3м",
        "volume": 34.632,
        "cell": "D241",
        "formula": null,
        "original": 34.632
      },
      {
        "name": "Засыпка траншеи ЩПС",
        "volume": 30.505,
        "cell": "D242",
        "formula": null,
        "original": 30.505
      }
    ],
    "pipes": [
      {
        "name": "Труба КОРСИС ПРО SN16 Ду=400мм l=8,51м",
        "length": 8.51,
        "area": 0.126,
        "diameter": 400.0,
        "method": "area",
        "count": 1,
        "cell": "D248",
        "formula": "8.51*0.126",
        "original": 1.07226
      },
      {
        "name": "Футляр ПЭ100 SDR17 Ду=710мм l=29,68м",
        "length": 29.68,
        "area": 0.396,
        "diameter": 710.0,
        "method": "area",
        "count": 1,
        "cell": "D249",
        "formula": "29.68*0.396",
        "original": 11.75328
      }
    ],
    "structures": [
      {
        "name": "Дождеприемный колодец Д23",
        "volume": 5.914,
        "excavation": 7.86562,
        "cell": "D252",
        "formula": null,
        "original": 5.914,
        "excavationSource": {
          "cell": "D253",
          "formula": "D252*133%",
          "original": 7.86562
        },
        "soilNote": "ИГЭ-1а (IV гр.) - 80,1%; ИГЭ-3б (II гр.) - 19,9%;"
      },
      {
        "name": "Дождеприемный колодец Д23'",
        "volume": 6.117,
        "excavation": 8.13561,
        "cell": "D254",
        "formula": null,
        "original": 6.117,
        "excavationSource": {
          "cell": "D255",
          "formula": "D254*133%",
          "original": 8.13561
        },
        "soilNote": "ИГЭ-1а (IV гр.) - 21,7%; ИГЭ-3б (II гр.) - 64,3%; ИГЭ-5б (I гр.) - 14%;"
      },
      {
        "name": "Перепадная камера КК2-23",
        "volume": 71.156,
        "excavation": 192.12120000000002,
        "cell": "D256",
        "formula": null,
        "original": 71.156,
        "excavationSource": {
          "cell": "D257",
          "formula": "D256*270%",
          "original": 192.12120000000002
        },
        "soilNote": "ИГЭ-3б (II гр.) - 41,4%; ИГЭ-5б (I гр.) - 58,6%;"
      }
    ],
    "groups": [
      14.4,
      47.3,
      1.2,
      37.1
    ],
    "notes": [
      {
        "label": "грунты I группы",
        "cell": "D235",
        "formula": "(D233*14.4%)",
        "original": 47.935008
      },
      {
        "label": "грунты II группы",
        "cell": "D236",
        "formula": "(D233*47.3%)",
        "original": 157.453186
      },
      {
        "label": "грунты III группы",
        "cell": "D237",
        "formula": "(D233*1.2%)",
        "original": 3.994584
      },
      {
        "label": "грунты IV группы",
        "cell": "D238",
        "formula": "(D233*37.1%)",
        "original": 123.499222
      }
    ],
    "sourceWarnings": [],
    "totalExcavation": 332.882,
    "soilNote": "Распределение выемки по грунтам: ИГЭ-1а (IV гр.) - 37,1%; ИГЭ-3б (II гр.) - 47,3%; ИГЭ-3в (III гр.) - 1,2%; ИГЭ-5б (I гр.) - 14,4%",
    "totalSource": {
      "cell": "D233",
      "formula": null,
      "original": 332.882
    },
    "originalBackfill": 2.99999999811007e-05,
    "backfillSource": {
      "cell": "D258",
      "formula": "D233-D243-D259",
      "original": 2.99999999811007e-05
    },
    "originalPitBackfill": 124.93543,
    "pitBackfillSource": {
      "cell": "D259",
      "formula": "(D253+D255+D257)-(D252+D254+D256)",
      "original": 124.93543
    }
  },
  {
    "id": "excel-260",
    "name": "Д24 - КК2-24",
    "source": {
      "file": "Копия Таблица грунтов (разработка траншеи).xlsx",
      "sheet": "ВР-37 ТКР10.1",
      "range": "A260:I287"
    },
    "materials": [
      {
        "name": "Подушка из ЩПС h=0,15м",
        "volume": 7.421,
        "cell": "D267",
        "formula": null,
        "original": 7.421
      },
      {
        "name": "Засыпка из ЩПС",
        "volume": 39.484,
        "cell": "D268",
        "formula": null,
        "original": 39.484
      },
      {
        "name": "Защитный слой из ЩПС h=0,3м",
        "volume": 34.742,
        "cell": "D269",
        "formula": null,
        "original": 34.742
      },
      {
        "name": "Засыпка траншеи ЩПС",
        "volume": 12.18,
        "cell": "D270",
        "formula": null,
        "original": 12.18
      }
    ],
    "pipes": [
      {
        "name": "Труба КОРСИС ПРО SN16 Ду=400мм l=8,51м",
        "length": 8.67,
        "area": 0.126,
        "diameter": 400.0,
        "method": "area",
        "count": 1,
        "cell": "D276",
        "formula": "8.67*0.126",
        "original": 1.09242
      },
      {
        "name": "Футляр ПЭ100 SDR17 Ду=710мм l=29,68м",
        "length": 29.68,
        "area": 0.396,
        "diameter": 710.0,
        "method": "area",
        "count": 1,
        "cell": "D277",
        "formula": "29.68*0.396",
        "original": 11.75328
      }
    ],
    "structures": [
      {
        "name": "Дождеприемный колодец Д24",
        "volume": 7.369,
        "excavation": 9.80077,
        "cell": "D280",
        "formula": null,
        "original": 7.369,
        "excavationSource": {
          "cell": "D281",
          "formula": "D280*133%",
          "original": 9.80077
        },
        "soilNote": "ИГЭ-1а (IV гр.) - 19,8%; ИГЭ-3б (II гр.) - 80,2%;"
      },
      {
        "name": "Дождеприемный колодец Д24'",
        "volume": 6.518,
        "excavation": 8.668940000000001,
        "cell": "D282",
        "formula": null,
        "original": 6.518,
        "excavationSource": {
          "cell": "D283",
          "formula": "D282*133%",
          "original": 8.668940000000001
        },
        "soilNote": "ИГЭ-1а (IV гр.) - 34,6%; ИГЭ-3б (II гр.) - 30,8%; ИГЭ-3в (I гр.) - 34,6%;"
      },
      {
        "name": "Перепадная камера КК2-24",
        "volume": 75.457,
        "excavation": 208.26131999999996,
        "cell": "D284",
        "formula": null,
        "original": 75.457,
        "excavationSource": {
          "cell": "D285",
          "formula": "(D284*276%)",
          "original": 208.26131999999996
        },
        "soilNote": "ИГЭ-3б (II гр.) - 29,4%; ИГЭ-5б (I гр.) - 70,6%;"
      }
    ],
    "groups": [
      3.1,
      34.2,
      17.6,
      45.1
    ],
    "notes": [
      {
        "label": "грунты I группы",
        "cell": "D263",
        "formula": "(D261*3.1%)",
        "original": 10.335524
      },
      {
        "label": "грунты II группы",
        "cell": "D264",
        "formula": "(D261*34.2%)",
        "original": 114.024168
      },
      {
        "label": "грунты III группы",
        "cell": "D265",
        "formula": "(D261*17.6%)",
        "original": 58.679104
      },
      {
        "label": "грунты IV группы",
        "cell": "D266",
        "formula": "(D261*45.1%)",
        "original": 150.365204
      }
    ],
    "sourceWarnings": [
      "B276 и D276: в названии длина 8,51 м, в формуле 8.67 м. Сохранена длина из формулы."
    ],
    "totalExcavation": 333.404,
    "soilNote": "Распределение выемки по грунтам: ИГЭ-1а (IV гр.) - 38,6%; ИГЭ-3б (II гр.) - 34,2%; ИГЭ-3в (III гр.) - 17,6%; ИГЭ-4а (IV гр.) - 6,5%; ИГЭ-5б (I гр.) - 3,1%",
    "totalSource": {
      "cell": "D261",
      "formula": null,
      "original": 333.404
    },
    "originalBackfill": 0.00027000000005728,
    "backfillSource": {
      "cell": "D286",
      "formula": "D261-D271-D287",
      "original": 0.00027000000005728
    },
    "originalPitBackfill": 137.38702999999995,
    "pitBackfillSource": {
      "cell": "D287",
      "formula": "(D281+D283+D285)-(D280+D282+D284)",
      "original": 137.38702999999995
    }
  },
  {
    "id": "excel-288",
    "name": "Д25 - КК2-25",
    "source": {
      "file": "Копия Таблица грунтов (разработка траншеи).xlsx",
      "sheet": "ВР-37 ТКР10.1",
      "range": "A288:I315"
    },
    "materials": [
      {
        "name": "Подушка из ЩПС h=0,15м",
        "volume": 7.446,
        "cell": "D295",
        "formula": null,
        "original": 7.446
      },
      {
        "name": "Засыпка из ЩПС",
        "volume": 39.567,
        "cell": "D296",
        "formula": null,
        "original": 39.567
      },
      {
        "name": "Защитный слой из ЩПС h=0,3м",
        "volume": 34.853,
        "cell": "D297",
        "formula": null,
        "original": 34.853
      },
      {
        "name": "Засыпка траншеи ЩПС",
        "volume": 30.151,
        "cell": "D298",
        "formula": null,
        "original": 30.151
      }
    ],
    "pipes": [
      {
        "name": "Труба КОРСИС ПРО SN16 Ду=400мм l=8,83м",
        "length": 8.83,
        "area": 0.126,
        "diameter": 400.0,
        "method": "area",
        "count": 1,
        "cell": "D304",
        "formula": "8.83*0.126",
        "original": 1.1125800000000001
      },
      {
        "name": "Футляр ПЭ100 SDR17 Ду=710мм l=29,68м",
        "length": 29.68,
        "area": 0.396,
        "diameter": 710.0,
        "method": "area",
        "count": 1,
        "cell": "D305",
        "formula": "29.68*0.396",
        "original": 11.75328
      }
    ],
    "structures": [
      {
        "name": "Дождеприемный колодец Д25",
        "volume": 6.993,
        "excavation": 9.300690000000001,
        "cell": "D308",
        "formula": null,
        "original": 6.993,
        "excavationSource": {
          "cell": "D309",
          "formula": "D308*133%",
          "original": 9.300690000000001
        },
        "soilNote": "ИГЭ-1а (IV гр.) - 40,6%; ИГЭ-3б (II гр.) - 10,9%; ИГЭ-4а (I гр.) - 48,5%;"
      },
      {
        "name": "Дождеприемный колодец Д25'",
        "volume": 6.816,
        "excavation": 9.06528,
        "cell": "D310",
        "formula": null,
        "original": 6.816,
        "excavationSource": {
          "cell": "D311",
          "formula": "D310*133%",
          "original": 9.06528
        },
        "soilNote": "ИГЭ-1а (IV гр.) - 31,6%; ИГЭ-3б (II гр.)- 32,1%; ИГЭ-5б (I гр.) - 36,3%;"
      },
      {
        "name": "Перепадная камера КК2-25",
        "volume": 79.449,
        "excavation": 190.67759999999998,
        "cell": "D312",
        "formula": null,
        "original": 79.449,
        "excavationSource": {
          "cell": "D313",
          "formula": "(D312*240%)",
          "original": 190.67759999999998
        },
        "soilNote": "ИГЭ-3б (II гр.) - 49,3%; ИГЭ-5 (I гр.) - 50,7%;"
      }
    ],
    "groups": [
      20.9,
      29.1,
      21.3,
      28.7
    ],
    "notes": [
      {
        "label": "грунты I группы",
        "cell": "D291",
        "formula": "(D289*20.9%)",
        "original": 69.790534
      },
      {
        "label": "грунты II группы",
        "cell": "D292",
        "formula": "(D289*29.1%)",
        "original": 97.17246600000001
      },
      {
        "label": "грунты III группы",
        "cell": "D293",
        "formula": "(D289*21.3%)",
        "original": 71.126238
      },
      {
        "label": "грунты IV группы",
        "cell": "D294",
        "formula": "(D289*28.7%)",
        "original": 95.836762
      }
    ],
    "sourceWarnings": [],
    "totalExcavation": 333.926,
    "soilNote": "Распределение выемки по грунтам: ИГЭ-1 (III гр.) - 6%; ИГЭ-1а (IV гр.) - 7,1%; ИГЭ-1б (II гр.) - 12,4%; ИГЭ-3б (II гр.) - 16,7%; ИГЭ-3в (III гр.) - 15,3%; ИГЭ-4а (IV гр.) - 21,6%; ИГЭ-5б (I гр.) - 5,6%; ИГЭ-7б (I гр.) - 15,3%",
    "totalSource": {
      "cell": "D289",
      "formula": null,
      "original": 333.926
    },
    "originalBackfill": -0.00042999999998016847,
    "backfillSource": {
      "cell": "D314",
      "formula": "D289-D299-D315",
      "original": -0.00042999999998016847
    },
    "originalPitBackfill": 115.78556999999999,
    "pitBackfillSource": {
      "cell": "D315",
      "formula": "(D309+D311+D313)-(D308+D310+D312)",
      "original": 115.78556999999999
    }
  },
  {
    "id": "excel-316",
    "name": "Д26 - КК2-26",
    "source": {
      "file": "Копия Таблица грунтов (разработка траншеи).xlsx",
      "sheet": "ВР-37 ТКР10.1",
      "range": "A316:I343"
    },
    "materials": [
      {
        "name": "Подушка из ЩПС h=0,15м",
        "volume": 7.471,
        "cell": "D323",
        "formula": null,
        "original": 7.471
      },
      {
        "name": "Засыпка из ЩПС",
        "volume": 39.649,
        "cell": "D324",
        "formula": null,
        "original": 39.649
      },
      {
        "name": "Защитный слой из ЩПС h=0,3м",
        "volume": 34.963,
        "cell": "D325",
        "formula": null,
        "original": 34.963
      },
      {
        "name": "Засыпка траншеи ЩПС",
        "volume": 20.147,
        "cell": "D326",
        "formula": null,
        "original": 20.147
      }
    ],
    "pipes": [
      {
        "name": "Труба КОРСИС ПРО SN16 Ду=400мм l=8,99м",
        "length": 8.99,
        "area": 0.126,
        "diameter": 400.0,
        "method": "area",
        "count": 1,
        "cell": "D332",
        "formula": "8.99*0.126",
        "original": 1.13274
      },
      {
        "name": "Футляр ПЭ100 SDR17 Ду=710мм l=29,68м",
        "length": 29.68,
        "area": 0.396,
        "diameter": 710.0,
        "method": "area",
        "count": 1,
        "cell": "D333",
        "formula": "29.68*0.396",
        "original": 11.75328
      }
    ],
    "structures": [
      {
        "name": "Дождеприемный колодец Д26",
        "volume": 6.993,
        "excavation": 9.300690000000001,
        "cell": "D336",
        "formula": null,
        "original": 6.993,
        "excavationSource": {
          "cell": "D337",
          "formula": "D336*133%",
          "original": 9.300690000000001
        },
        "soilNote": "ИГЭ-1 (III гр.) - 45,2%; ИГЭ-4а - 17,6%; ИГЭ-7б - 37,2%;"
      },
      {
        "name": "Дождеприемный колодец Д26'",
        "volume": 6.816,
        "excavation": 9.06528,
        "cell": "D338",
        "formula": null,
        "original": 6.816,
        "excavationSource": {
          "cell": "D339",
          "formula": "D338*133%",
          "original": 9.06528
        },
        "soilNote": "ИГЭ-1б (II гр.) - 26,2%; ИГЭ-4а - 39,1%; ИГЭ-7б - 34,7%;"
      },
      {
        "name": "Перепадная камера КК2-26",
        "volume": 73.614,
        "excavation": 200.96622000000002,
        "cell": "D340",
        "formula": null,
        "original": 73.614,
        "excavationSource": {
          "cell": "D341",
          "formula": "(D340*273%)",
          "original": 200.96622000000002
        },
        "soilNote": "ИГЭ-3б (II гр.) - 67,4%; ИГЭ-5 (I гр.) - 6,1%; ИГЭ-7а - 26,5%"
      }
    ],
    "groups": [
      43.4,
      18.7,
      29.6,
      8.3
    ],
    "notes": [
      {
        "label": "грунты I группы",
        "cell": "D319",
        "formula": "(D317*43.4%)",
        "original": 145.150432
      },
      {
        "label": "грунты II группы",
        "cell": "D320",
        "formula": "(D317*18.7%)",
        "original": 62.541776
      },
      {
        "label": "грунты III группы",
        "cell": "D321",
        "formula": "(D317*29.6%)",
        "original": 98.99660800000001
      },
      {
        "label": "грунты IV группы",
        "cell": "D322",
        "formula": "(D317*8.3%)",
        "original": 27.759184
      }
    ],
    "sourceWarnings": [],
    "totalExcavation": 334.448,
    "soilNote": "Распределение выемки по грунтам: ИГЭ-1 (III гр.) - 29,6%; ИГЭ-1б (II гр.) - 18,7%; ИГЭ-4а (IV гр.) - 8,3%; ИГЭ-7б (I гр.) - 43,4%",
    "totalSource": {
      "cell": "D317",
      "formula": null,
      "original": 334.448
    },
    "originalBackfill": -0.00021000000003823516,
    "backfillSource": {
      "cell": "D342",
      "formula": "D317-D327-D343",
      "original": -0.00021000000003823516
    },
    "originalPitBackfill": 131.90919000000002,
    "pitBackfillSource": {
      "cell": "D343",
      "formula": "(D337+D339+D341)-(D336+D338+D340)",
      "original": 131.90919000000002
    }
  },
  {
    "id": "excel-344",
    "name": "Д27 - КК2-27",
    "source": {
      "file": "Копия Таблица грунтов (разработка траншеи).xlsx",
      "sheet": "ВР-37 ТКР10.1",
      "range": "A344:I370"
    },
    "materials": [
      {
        "name": "Подушка из ЩПС h=0,15м",
        "volume": 7.745,
        "cell": "D350",
        "formula": null,
        "original": 7.745
      },
      {
        "name": "Засыпка из ЩПС",
        "volume": 36.468,
        "cell": "D351",
        "formula": null,
        "original": 36.468
      },
      {
        "name": "Защитный слой из ЩПС h=0,3м",
        "volume": 30.2,
        "cell": "D352",
        "formula": null,
        "original": 30.2
      },
      {
        "name": "Засыпка траншеи ЩПС",
        "volume": 139.678,
        "cell": "D353",
        "formula": null,
        "original": 139.678
      }
    ],
    "pipes": [
      {
        "name": "Труба КОРСИС ПРО SN16 Ду=400мм l=9,14м",
        "length": 9.14,
        "area": 0.126,
        "diameter": 400.0,
        "method": "area",
        "count": 1,
        "cell": "D359",
        "formula": "9.14*0.126",
        "original": 1.15164
      },
      {
        "name": "Футляр ПЭ100 SDR17 Ду=710мм l=29,68м",
        "length": 29.68,
        "area": 0.396,
        "diameter": 710.0,
        "method": "area",
        "count": 1,
        "cell": "D360",
        "formula": "29.68*0.396",
        "original": 11.75328
      }
    ],
    "structures": [
      {
        "name": "Дождеприемный колодец Д26",
        "volume": 6.714,
        "excavation": 8.929620000000002,
        "cell": "D363",
        "formula": null,
        "original": 6.714,
        "excavationSource": {
          "cell": "D364",
          "formula": "D363*133%",
          "original": 8.929620000000002
        },
        "soilNote": "ИГЭ-1 (III гр.) - 75,2%; ИГЭ-7б - 24,8%;"
      },
      {
        "name": "Дождеприемный колодец Д26'",
        "volume": 7.011,
        "excavation": 9.32463,
        "cell": "D365",
        "formula": null,
        "original": 7.011,
        "excavationSource": {
          "cell": "D366",
          "formula": "D365*133%",
          "original": 9.32463
        },
        "soilNote": "ИГЭ-1б (II гр.) - 100%;"
      },
      {
        "name": "Линейный колодец КК2-27",
        "volume": 59.792,
        "excavation": 89.688,
        "cell": "D367",
        "formula": null,
        "original": 59.792,
        "excavationSource": {
          "cell": "D368",
          "formula": "(D367*150%)",
          "original": 89.688
        },
        "soilNote": "ИГЭ-1 (III гр.) - 78,2%; ИГЭ-5 (I гр.) - 21,8%;"
      }
    ],
    "groups": [
      24.5,
      54.2,
      21.3,
      0
    ],
    "notes": [
      {
        "label": "грунты I группы",
        "cell": "D347",
        "formula": "(D345*24.5%)",
        "original": 82.05981
      },
      {
        "label": "грунты II группы",
        "cell": "D348",
        "formula": "(D345*54.2%)",
        "original": 181.536396
      },
      {
        "label": "грунты III группы",
        "cell": "D349",
        "formula": "(D345*21.3%)",
        "original": 71.341794
      }
    ],
    "sourceWarnings": [],
    "totalExcavation": 334.938,
    "soilNote": "Распределение выемки по грунтам: ИГЭ-1 (III гр.) - 21,3%; ИГЭ-1б (II гр.) - 54,2%; ИГЭ-7б (I гр.) - 24,5%",
    "totalSource": {
      "cell": "D345",
      "formula": null,
      "original": 334.938
    },
    "originalBackfill": -0.0001700000000255386,
    "backfillSource": {
      "cell": "D369",
      "formula": "D345-D354-D370",
      "original": -0.0001700000000255386
    },
    "originalPitBackfill": 34.425250000000005,
    "pitBackfillSource": {
      "cell": "D370",
      "formula": "(D364+D366+D368)-(D363+D365+D367)",
      "original": 34.425250000000005
    }
  },
  {
    "id": "excel-371",
    "name": "КК2-31 - КК2-15",
    "source": {
      "file": "Копия Таблица грунтов (разработка траншеи).xlsx",
      "sheet": "ВР-37 ТКР10.1",
      "range": "A371:I391"
    },
    "materials": [
      {
        "name": "Подушка из ЩПС h=0,15м",
        "volume": 2.608,
        "cell": "D375",
        "formula": null,
        "original": 2.608
      },
      {
        "name": "Засыпка из ЩПС",
        "volume": 8.512,
        "cell": "D376",
        "formula": null,
        "original": 8.512
      },
      {
        "name": "Защитный слой из ЩПС h=0,3м",
        "volume": 11.426,
        "cell": "D377",
        "formula": null,
        "original": 11.426
      }
    ],
    "pipes": [
      {
        "name": "Труба КОРСИС ПРО SN16 Ду=400мм l=17,57м",
        "length": 17.57,
        "area": 0.126,
        "diameter": 400.0,
        "method": "area",
        "count": 1,
        "cell": "D383",
        "formula": "17.57*0.126",
        "original": 2.21382
      }
    ],
    "structures": [
      {
        "name": "Дождеприемный колодец КК2-31",
        "volume": 6.215,
        "excavation": 8.26595,
        "cell": "D386",
        "formula": null,
        "original": 6.215,
        "excavationSource": {
          "cell": "D387",
          "formula": "D386*133%",
          "original": 8.26595
        },
        "soilNote": "ИГЭ-1а (IV гр.) - 100%"
      },
      {
        "name": "Поворотный колодец КК2-15",
        "volume": 7.265,
        "excavation": 9.22655,
        "cell": "D388",
        "formula": null,
        "original": 7.265,
        "excavationSource": {
          "cell": "D389",
          "formula": "D388*127%",
          "original": 9.22655
        },
        "soilNote": "ИГЭ-1а (IV гр.) - 100%"
      }
    ],
    "groups": [
      0,
      0,
      0,
      100.0
    ],
    "notes": [
      {
        "label": "грунты IV группы",
        "cell": "D374",
        "formula": "(D372*100%)",
        "original": 54.034
      }
    ],
    "sourceWarnings": [],
    "totalExcavation": 54.034,
    "soilNote": "Распределение выемки по грунтам: ИГЭ-1а (IV гр.) - 100%",
    "totalSource": {
      "cell": "D372",
      "formula": null,
      "original": 54.034
    },
    "originalBackfill": 11.781680000000005,
    "backfillSource": {
      "cell": "D390",
      "formula": "D372-D378-D391",
      "original": 11.781680000000005
    },
    "originalPitBackfill": 4.012499999999999,
    "pitBackfillSource": {
      "cell": "D391",
      "formula": "(D387+D389)-(D386+D388)",
      "original": 4.012499999999999
    }
  },
  {
    "id": "excel-392",
    "name": "Д29 - КК2-29",
    "source": {
      "file": "Копия Таблица грунтов (разработка траншеи).xlsx",
      "sheet": "ВР-37 ТКР10.1",
      "range": "A392:I413"
    },
    "materials": [
      {
        "name": "Подушка из ЩПС h=0,15м",
        "volume": 0.571,
        "cell": "D396",
        "formula": null,
        "original": 0.571
      },
      {
        "name": "Засыпка из ЩПС",
        "volume": 3.305,
        "cell": "D397",
        "formula": null,
        "original": 3.305
      },
      {
        "name": "Защитный слой из ЩПС h=0,3м",
        "volume": 2.713,
        "cell": "D398",
        "formula": null,
        "original": 2.713
      },
      {
        "name": "Засыпка траншеи ЩПС",
        "volume": 0.386,
        "cell": "D399",
        "formula": null,
        "original": 0.386
      }
    ],
    "pipes": [
      {
        "name": "Футляр ПЭ100 SDR17 Ду=710мм l=4м",
        "length": 4.0,
        "area": 0.396,
        "diameter": 710.0,
        "method": "area",
        "count": 1,
        "cell": "D405",
        "formula": "4*0.396",
        "original": 1.584
      }
    ],
    "structures": [
      {
        "name": "Дождеприемный колодец Д29",
        "volume": 5.416,
        "excavation": 5.52432,
        "cell": "D408",
        "formula": null,
        "original": 5.416,
        "excavationSource": {
          "cell": "D409",
          "formula": "D408*102%",
          "original": 5.52432
        },
        "soilNote": "ИГЭ-1б (II гр.) - 100%"
      },
      {
        "name": "Поворотный колодец КК2-29",
        "volume": 13.126,
        "excavation": 14.701120000000001,
        "cell": "D410",
        "formula": null,
        "original": 13.126,
        "excavationSource": {
          "cell": "D411",
          "formula": "D410*112%",
          "original": 14.701120000000001
        },
        "soilNote": "ИГЭ-1а (IV гр.) - 50%; ИГЭ-1б (II гр.) - 50%"
      }
    ],
    "groups": [
      0,
      0,
      0,
      100.0
    ],
    "notes": [
      {
        "label": "грунты IV группы",
        "cell": "D395",
        "formula": "(D393*100%)",
        "original": 28.784
      }
    ],
    "sourceWarnings": [
      "Группы грунтов в примечании E и строках расчёта D расходятся. В расчёт перенесены группы из строк D; исходное примечание сохранено.",
      "Боковая колонка I400: 3.67000 м³, по подробным строкам 6.40400 м³ (щпс без подушки). В системе используется сумма подробных строк, а не боковой итог."
    ],
    "totalExcavation": 28.784,
    "soilNote": "Распределение выемки по грунтам: ИГЭ-1б (II гр.) - 100%",
    "totalSource": {
      "cell": "D393",
      "formula": null,
      "original": 28.784
    },
    "originalBackfill": -0.0004400000000046589,
    "backfillSource": {
      "cell": "D412",
      "formula": "D393-D400-D413",
      "original": -0.0004400000000046589
    },
    "originalPitBackfill": 1.683440000000001,
    "pitBackfillSource": {
      "cell": "D413",
      "formula": "(D409+D411)-(D408+D410)",
      "original": 1.683440000000001
    }
  },
  {
    "id": "excel-414",
    "name": "Д30 - КК2-30",
    "source": {
      "file": "Копия Таблица грунтов (разработка траншеи).xlsx",
      "sheet": "ВР-37 ТКР10.1",
      "range": "A414:I435"
    },
    "materials": [
      {
        "name": "Подушка из ЩПС h=0,15м",
        "volume": 0.775,
        "cell": "D418",
        "formula": null,
        "original": 0.775
      },
      {
        "name": "Засыпка из ЩПС",
        "volume": 4.485,
        "cell": "D419",
        "formula": null,
        "original": 4.485
      },
      {
        "name": "Защитный слой из ЩПС h=0,3м",
        "volume": 3.682,
        "cell": "D420",
        "formula": null,
        "original": 3.682
      },
      {
        "name": "Засыпка траншеи ЩПС",
        "volume": 5.945,
        "cell": "D421",
        "formula": null,
        "original": 5.945
      }
    ],
    "pipes": [
      {
        "name": "Футляр ПЭ100 SDR17 Ду=710мм l=3,80м",
        "length": 3.8,
        "area": 0.396,
        "diameter": 710.0,
        "method": "area",
        "count": 1,
        "cell": "D427",
        "formula": "3.8*0.396",
        "original": 1.5048
      }
    ],
    "structures": [
      {
        "name": "Дождеприемный колодец Д30",
        "volume": 6.117,
        "excavation": 6.23934,
        "cell": "D430",
        "formula": null,
        "original": 6.117,
        "excavationSource": {
          "cell": "D431",
          "formula": "D430*102%",
          "original": 6.23934
        },
        "soilNote": "ИГЭ-1 (III гр.) - 100%"
      },
      {
        "name": "Поворотный колодец КК2-30",
        "volume": 14.046,
        "excavation": 16.433819999999997,
        "cell": "D432",
        "formula": null,
        "original": 14.046,
        "excavationSource": {
          "cell": "D433",
          "formula": "D432*117%",
          "original": 16.433819999999997
        },
        "soilNote": "ИГЭ-1 (III гр.) - 50%; ИГЭ-1а (IV гр.) - 50%"
      }
    ],
    "groups": [
      0,
      0,
      100.0,
      0
    ],
    "notes": [
      {
        "label": "грунты III группы",
        "cell": "D417",
        "formula": "(D415*100%)",
        "original": 39.065
      }
    ],
    "sourceWarnings": [],
    "totalExcavation": 39.065,
    "soilNote": "Распределение выемки по грунтам: ИГЭ-1 (III гр.) - 100%",
    "totalSource": {
      "cell": "D415",
      "formula": null,
      "original": 39.065
    },
    "originalBackfill": 4.0000000002038405e-05,
    "backfillSource": {
      "cell": "D434",
      "formula": "D415-D422-D435",
      "original": 4.0000000002038405e-05
    },
    "originalPitBackfill": 2.5101599999999955,
    "pitBackfillSource": {
      "cell": "D435",
      "formula": "(D431+D433)-(D430+D432)",
      "original": 2.5101599999999955
    }
  }
];
