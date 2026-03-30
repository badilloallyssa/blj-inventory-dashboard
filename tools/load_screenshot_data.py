"""
Load sales data directly from verified screenshot numbers into Sales_Data tab.
This replaces the migrate script approach since the old sheet column mapping
was reading incorrect positions for some SKUs.

Usage:
    python3 tools/load_screenshot_data.py --dry-run
    python3 tools/load_screenshot_data.py
"""
import sys
import os
import argparse
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sheets_client import get_sheets_service, get_sheet_id, write_tab

# ── Sales data from verified screenshots ─────────────────────────────────────
# Format: {sku_id: {year: {month_num: {warehouse: units}}}}
# Warehouses: US (Shopify), Amazon_US_FBA, AU, CA, UK, EU
# Zeros are omitted — only non-zero values stored

SALES_DATA = {
    'EIDJ2100': {  # Teen Journal
        'name': 'Teen Journal',
        2024: {
            1:  {'US': 1072,  'Amazon_US_FBA': 1713, 'AU': 720,  'CA': 701,  'UK': 1332},
            2:  {'US': 623,   'Amazon_US_FBA': 1584, 'AU': 427,  'CA': 349,  'UK': 2357},
            3:  {'US': 541,   'Amazon_US_FBA': 1585, 'AU': 635,  'CA': 156,  'UK': 1112},
            4:  {'US': 456,   'Amazon_US_FBA': 1116, 'AU': 328,  'CA': 71,   'UK': 638},
            5:  {'US': 1054,  'Amazon_US_FBA': 1880, 'AU': 553,  'CA': 221,  'UK': 697},
            6:  {'US': 440,   'Amazon_US_FBA': 1231, 'AU': 346,  'CA': 328,  'UK': 526},
            7:  {'US': 614,   'Amazon_US_FBA': 1302, 'AU': 330,  'CA': 69,   'UK': 368},
            8:  {'US': 517,   'Amazon_US_FBA': 1291, 'AU': 397,  'CA': 181,  'UK': 227},
            9:  {'US': 495,   'Amazon_US_FBA': 1459, 'AU': 576,  'CA': 166,  'UK': 281},
            10: {'US': 515,   'Amazon_US_FBA': 888,  'AU': 307,  'CA': 154,  'UK': 346},
            11: {'US': 1644,  'Amazon_US_FBA': 1982, 'AU': 1501, 'CA': 737,  'UK': 744},
            12: {'US': 4742,  'Amazon_US_FBA': 4858, 'AU': 2085, 'CA': 752,  'UK': 2381},
        },
        2026: {
            1:  {'US': 693,  'Amazon_US_FBA': 895,  'AU': 485, 'CA': 200, 'UK': 338, 'EU': 20},
            2:  {'US': 513,  'Amazon_US_FBA': 794,  'AU': 327, 'CA': 159, 'UK': 723, 'EU': 101},
        },
        2025: {
            1:  {'US': 1238,  'Amazon_US_FBA': 1162, 'AU': 589,  'CA': 341,  'UK': 1539, 'EU': 298},
            2:  {'US': 1061,  'Amazon_US_FBA': 1334, 'AU': 1105, 'CA': 266,  'UK': 1231, 'EU': 235},
            3:  {'US': 807,   'Amazon_US_FBA': 1197, 'AU': 790,  'CA': 265,  'UK': 703,  'EU': 158},
            4:  {'US': 671,   'Amazon_US_FBA': 1382, 'AU': 214,  'CA': 80,   'UK': 166,  'EU': 46},
            5:  {'US': 754,   'Amazon_US_FBA': 1293, 'AU': 673,  'CA': 191,  'UK': 292,  'EU': 86},
            6:  {'US': 999,   'Amazon_US_FBA': 1671, 'AU': 882,  'CA': 575,  'UK': 354,  'EU': 110},
            7:  {'US': 1025,  'Amazon_US_FBA': 1221, 'AU': 644,  'CA': 253,  'UK': 282,  'EU': 204},
            8:  {'US': 648,   'Amazon_US_FBA': 809,  'AU': 589,  'CA': 129,  'UK': 123,  'EU': 92},
            9:  {'US': 704,   'Amazon_US_FBA': 880,  'AU': 273,  'CA': 250,  'UK': 41,   'EU': 29},
            10: {'US': 853,   'Amazon_US_FBA': 110,  'AU': 683,  'CA': 167,  'UK': 7,    'EU': 12},
            11: {'US': 1768,  'Amazon_US_FBA': 1718, 'AU': 1680, 'CA': 431,  'UK': 1260, 'EU': 222},
            12: {'US': 2249,  'Amazon_US_FBA': 3294, 'AU': 1206, 'CA': 458,  'UK': 468,  'EU': 239},
        },
    },

    'EIDJ4100': {  # Kids Journal
        'name': 'Kids Journal',
        2024: {
            1:  {'US': 2695,  'Amazon_US_FBA': 2727, 'AU': 159,  'CA': 437,  'UK': 4238},
            2:  {'US': 2203,  'Amazon_US_FBA': 2747, 'AU': 662,  'CA': 486,  'UK': 2663},
            3:  {'US': 2095,  'Amazon_US_FBA': 2908, 'AU': 1080, 'CA': 428,  'UK': 1710},
            4:  {'US': 1236,  'Amazon_US_FBA': 2359, 'AU': 1014, 'CA': 267,  'UK': 857},
            5:  {'US': 2174,  'Amazon_US_FBA': 1832, 'AU': 1089, 'CA': 666,  'UK': 846},
            6:  {'US': 1214,  'Amazon_US_FBA': 1344, 'AU': 792,  'CA': 416,  'UK': 531},
            7:  {'US': 794,   'Amazon_US_FBA': 1582, 'AU': 762,  'CA': 224,  'UK': 799},
            8:  {'US': 1054,  'Amazon_US_FBA': 1456, 'AU': 664,  'CA': 339,  'UK': 384},
            9:  {'US': 1022,  'Amazon_US_FBA': 1520, 'AU': 831,  'CA': 237,  'UK': 378},
            10: {'US': 724,   'Amazon_US_FBA': 1345, 'AU': 679,  'CA': 168,  'UK': 331},
            11: {'US': 2028,  'Amazon_US_FBA': 2176, 'AU': 2717, 'CA': 811,  'UK': 1221},
            12: {'US': 7742,  'Amazon_US_FBA': 6862, 'AU': 3160, 'CA': 911,  'UK': 1282},
        },
        2025: {
            1:  {'US': 1305,  'Amazon_US_FBA': 1325, 'AU': 616,  'CA': 370,  'UK': 516,  'EU': 101},
            2:  {'US': 645,   'Amazon_US_FBA': 1479, 'AU': 897,  'CA': 199,  'UK': 373,  'EU': 89},
            3:  {'US': 728,   'Amazon_US_FBA': 1253, 'AU': 656,  'CA': 215,  'UK': 234,  'EU': 98},
            4:  {'US': 1226,  'Amazon_US_FBA': 1957, 'AU': 578,  'CA': 170,  'UK': 104,  'EU': 112},
            5:  {'US': 801,   'Amazon_US_FBA': 1094, 'AU': 544,  'CA': 252,  'UK': 198,  'EU': 202},
            6:  {'US': 959,   'Amazon_US_FBA': 960,  'AU': 600,  'CA': 357,  'UK': 124,  'EU': 247},
            7:  {'US': 811,   'Amazon_US_FBA': 670,  'AU': 498,  'CA': 175,  'UK': 81,   'EU': 349},
            8:  {'US': 483,   'Amazon_US_FBA': 562,  'AU': 269,  'CA': 101,  'UK': 37,   'EU': 49},
            9:  {'US': 578,   'Amazon_US_FBA': 578,  'AU': 288,  'CA': 186,  'UK': 49,   'EU': 110},
            10: {'US': 897,   'Amazon_US_FBA': 912,  'AU': 574,  'CA': 177,  'UK': 33,   'EU': 177},
            11: {'US': 6699,  'Amazon_US_FBA': 1618, 'AU': 4180, 'CA': 1093, 'UK': 3127, 'EU': 1009},
            12: {'US': 7994,  'Amazon_US_FBA': 4378, 'AU': 3569, 'CA': 1278, 'UK': 2027, 'EU': 1002},
        },
        2026: {
            1:  {'US': 944,  'Amazon_US_FBA': 1254, 'AU': 716, 'CA': 236, 'UK': 287, 'EU': 18},
            2:  {'US': 662,  'Amazon_US_FBA': 1016, 'AU': 395, 'CA': 191, 'UK': 410, 'EU': 105},
        },
    },

    'EIDJ5100': {  # Daily Journal Teal
        'name': 'Daily Journal Teal',
        2024: {
            1:  {'US': 1237,  'Amazon_US_FBA': 1022, 'AU': 422,  'CA': 173,  'UK': 726},
            2:  {'US': 822,   'Amazon_US_FBA': 998,  'AU': 361,  'CA': 203,  'UK': 546},
            3:  {'US': 626,   'Amazon_US_FBA': 849,  'AU': 415,  'CA': 209,  'UK': 721},
            4:  {'US': 1103,  'Amazon_US_FBA': 1122, 'AU': 866,  'CA': 308,  'UK': 1563},
            5:  {'US': 1359,  'Amazon_US_FBA': 736,  'AU': 832,  'CA': 473,  'UK': 167},
            6:  {'US': 745,   'Amazon_US_FBA': 736,  'AU': 829,  'CA': 234,  'UK': 111},
            7:  {'US': 1336,  'Amazon_US_FBA': 1047, 'AU': 1072, 'CA': 236,  'UK': 572},
            8:  {'US': 1385,  'Amazon_US_FBA': 907,  'AU': 775,  'CA': 204,  'UK': 1433},
            9:  {'US': 1189,  'Amazon_US_FBA': 869,  'AU': 757,  'CA': 327,  'UK': 1414},
            10: {'US': 838,   'Amazon_US_FBA': 796,  'AU': 642,  'CA': 184,  'UK': 1082},
            11: {'US': 1602,  'Amazon_US_FBA': 1403, 'AU': 1778, 'CA': 372,  'UK': 1543},
            12: {'US': 3893,  'Amazon_US_FBA': 2820, 'AU': 1657, 'CA': 436,  'UK': 2373},
        },
        2025: {
            1:  {'US': 948,   'Amazon_US_FBA': 1082, 'AU': 465,  'CA': 256,  'UK': 1325, 'EU': 117},
            2:  {'US': 994,   'Amazon_US_FBA': 833,  'AU': 724,  'CA': 212,  'UK': 782,  'EU': 111},
            3:  {'US': 687,   'Amazon_US_FBA': 870,  'AU': 524,  'CA': 140,  'UK': 598,  'EU': 46},
            4:  {'US': 476,   'Amazon_US_FBA': 609,  'AU': 197,  'CA': 270,  'UK': 208,  'EU': 23},
            5:  {'US': 583,   'Amazon_US_FBA': 459,  'AU': 254,  'CA': 208,  'UK': 278,  'EU': 24},
            6:  {'US': 303,   'Amazon_US_FBA': 376,  'AU': 229,  'CA': 159,  'UK': 237,  'EU': 19},
            7:  {'US': 243,   'Amazon_US_FBA': 326,  'AU': 205,  'CA': 147,  'UK': 173,  'EU': 80},
            8:  {'US': 213,   'Amazon_US_FBA': 411,  'AU': 130,  'CA': 47,   'UK': 68,   'EU': 37},
            9:  {'US': 209,   'Amazon_US_FBA': 377,  'AU': 152,  'CA': 118,  'UK': 103,  'EU': 34},
            10: {'US': 628,   'Amazon_US_FBA': 382,  'AU': 178,  'CA': 64,   'UK': 118,  'EU': 34},
            11: {'US': 901,   'Amazon_US_FBA': 960,  'AU': 796,  'CA': 302,  'UK': 642,  'EU': 173},
            12: {'US': 1827,  'Amazon_US_FBA': 1786, 'AU': 730,  'CA': 394,  'UK': 569,  'EU': 189},
        },
        2026: {
            1:  {'US': 673,  'Amazon_US_FBA': 508,  'AU': 467, 'CA': 205, 'UK': 363, 'EU': 14},
            2:  {'US': 357,  'Amazon_US_FBA': 415,  'AU': 191, 'CA': 143, 'UK': 491, 'EU': 39},
        },
    },

    'EIDJ5200': {  # Daily Journal Green
        'name': 'Daily Journal Green',
        2024: {
            1:  {'US': 407,   'Amazon_US_FBA': 489,  'AU': 136,  'CA': 74,   'UK': 216},
            2:  {'US': 255,   'Amazon_US_FBA': 298,  'AU': 130,  'CA': 73,   'UK': 186},
            3:  {'US': 141,   'Amazon_US_FBA': 99,   'AU': 100,  'CA': 26,   'UK': 121},
            4:  {'US': 925,   'Amazon_US_FBA': 448,  'AU': 328,  'CA': 203,  'UK': 2044},
            5:  {'US': 682,   'Amazon_US_FBA': 486,  'AU': 288,  'CA': 133,  'UK': 763},
            6:  {'US': 280,   'Amazon_US_FBA': 674,  'AU': 245,  'CA': 72,   'UK': 195},
            7:  {'US': 445,   'Amazon_US_FBA': 628,  'AU': 352,  'CA': 75,   'UK': 254},
            8:  {'US': 446,   'Amazon_US_FBA': 630,  'AU': 231,  'CA': 66,   'UK': 320},
            9:  {'US': 350,   'Amazon_US_FBA': 451,  'AU': 222,  'CA': 75,   'UK': 348},
            10: {'US': 365,   'Amazon_US_FBA': 533,  'AU': 189,  'CA': 59,   'UK': 350},
            11: {'US': 694,   'Amazon_US_FBA': 952,  'AU': 611,  'CA': 152,  'UK': 611},
            12: {'US': 1287,  'Amazon_US_FBA': 1899, 'AU': 412,  'CA': 108,  'UK': 994},
        },
        2025: {
            1:  {'US': 452,   'Amazon_US_FBA': 505,  'AU': 191,  'CA': 99,   'UK': 683,  'EU': 57},
            2:  {'US': 483,   'Amazon_US_FBA': 521,  'AU': 211,  'CA': 62,   'UK': 343,  'EU': 37},
            3:  {'US': 340,   'Amazon_US_FBA': 599,  'AU': 225,  'CA': 68,   'UK': 235,  'EU': 20},
            4:  {'US': 276,   'Amazon_US_FBA': 482,  'AU': 93,   'CA': 31,   'UK': 82,   'EU': 11},
            5:  {'US': 129,   'Amazon_US_FBA': 387,  'AU': 97,   'CA': 31,   'UK': 130,  'EU': 65},
            6:  {'US': 125,   'Amazon_US_FBA': 392,  'AU': 71,   'CA': 30,   'UK': 98,   'EU': 56},
            7:  {'US': 119,   'Amazon_US_FBA': 247,  'AU': 73,   'CA': 29,   'UK': 89,   'EU': 100},
            8:  {'US': 67,    'Amazon_US_FBA': 258,  'AU': 49,   'CA': 22,   'UK': 27,   'EU': 26},
            9:  {'US': 63,    'Amazon_US_FBA': 304,  'AU': 41,   'CA': 21,   'UK': 40,   'EU': 16},
            10: {'US': 54,    'Amazon_US_FBA': 333,  'AU': 32,   'CA': 17,   'UK': 50,   'EU': 18},
            11: {'US': 1003,  'Amazon_US_FBA': 723,  'AU': 243,  'CA': 125,  'UK': 239,  'EU': 110},
            12: {'US': 1015,  'Amazon_US_FBA': 1131, 'AU': 193,  'CA': 150,  'UK': 200,  'EU': 111},
        },
        2026: {
            1:  {'US': 227,  'Amazon_US_FBA': 304,  'AU': 139, 'CA': 63,  'UK': 114, 'EU': 13},
            2:  {'US': 104,  'Amazon_US_FBA': 316,  'AU': 38,  'CA': 40,  'UK': 146, 'EU': 23},
        },
    },

    'EIDJ5000': {  # Adult Journal
        'name': 'Adult Journal',
        2024: {
            1:  {'US': 1487,  'Amazon_US_FBA': 905,  'AU': 657,  'CA': 500,  'UK': 114},
            2:  {'US': 245,   'Amazon_US_FBA': 470,  'AU': 236,  'CA': 206,  'UK': 99},
            3:  {'US': 165,   'Amazon_US_FBA': 323,  'AU': 192,  'CA': 119,  'UK': 282},
            4:  {'US': 181,   'Amazon_US_FBA': 452,  'AU': 189,  'CA': 63,   'UK': 472},
            5:  {'US': 465,   'Amazon_US_FBA': 589,  'AU': 259,  'CA': 89,   'UK': 547},
            6:  {'US': 369,   'Amazon_US_FBA': 420,  'AU': 226,  'CA': 83,   'UK': 524},
            7:  {'US': 331,   'Amazon_US_FBA': 429,  'AU': 209,  'CA': 73,   'UK': 323},
            8:  {'US': 199,   'Amazon_US_FBA': 387,  'AU': 148,  'CA': 23,   'UK': 259},
            9:  {'US': 163,   'Amazon_US_FBA': 313,  'AU': 145,  'CA': 57,   'UK': 186},
            10: {'US': 103,   'Amazon_US_FBA': 233,  'AU': 116,  'CA': 39,   'UK': 315},
            11: {'US': 901,   'Amazon_US_FBA': 505,  'AU': 654,  'CA': 350,  'UK': 1135},
            12: {'US': 2854,  'Amazon_US_FBA': 1607, 'AU': 1401, 'CA': 366,  'UK': 2842},
        },
        2025: {
            1:  {'US': 460,   'Amazon_US_FBA': 488,  'AU': 376,  'CA': 261,  'UK': 761,  'EU': 72},
            2:  {'US': 226,   'Amazon_US_FBA': 226,  'AU': 182,  'CA': 38,   'UK': 341,  'EU': 38},
            3:  {'US': 107,   'Amazon_US_FBA': 208,  'AU': 131,  'CA': 83,   'UK': 149,  'EU': 17},
            4:  {'US': 91,    'Amazon_US_FBA': 216,  'AU': 61,   'CA': 13,   'UK': 33,   'EU': 7},
            5:  {'US': 143,   'Amazon_US_FBA': 250,  'AU': 72,   'CA': 22,   'UK': 25,   'EU': 25},
            6:  {'US': 173,   'Amazon_US_FBA': 198,  'AU': 137,  'CA': 39,   'UK': 28,   'EU': 52},
            7:  {'US': 80,    'Amazon_US_FBA': 137,  'AU': 61,   'CA': 28,   'UK': 24,   'EU': 358},
            8:  {'US': 91,    'Amazon_US_FBA': 267,  'AU': 89,   'CA': 32,   'UK': 11,   'EU': 6},
            9:  {'US': 89,    'Amazon_US_FBA': 123,  'AU': 55,   'CA': 18,   'UK': 13,   'EU': 14},
            10: {'US': 324,   'Amazon_US_FBA': 273,  'AU': 35,   'CA': 21,   'UK': 9,    'EU': 8},
            11: {'US': 466,   'Amazon_US_FBA': 493,  'AU': 357,  'CA': 135,  'UK': 200,  'EU': 67},
            12: {'US': 691,   'Amazon_US_FBA': 602,  'AU': 295,  'CA': 182,  'UK': 130,  'EU': 75},
        },
        2026: {
            1:  {'US': 228,  'Amazon_US_FBA': 213,  'AU': 97,  'CA': 70,  'UK': 54,  'EU': 16},
            2:  {'US': 139,  'Amazon_US_FBA': 136,  'AU': 55,  'CA': 67,  'UK': 213, 'EU': 38},
        },
    },

    'EIDC2000': {  # Sharing Joy Conversation Cards
        'name': 'Sharing Joy Cards',
        2024: {
            # Jan-Aug = 0, launched Sep 2024
            9:  {'US': 1465,  'AU': 481,  'CA': 281,  'UK': 276},
            10: {'US': 1532,  'Amazon_US_FBA': 100,  'AU': 309,  'CA': 205,  'UK': 204},
            11: {'US': 1599,  'Amazon_US_FBA': 842,  'AU': 854,  'CA': 385,  'UK': 683},
            12: {'US': 4642,  'Amazon_US_FBA': 2500, 'AU': 1173, 'CA': 390,  'UK': 1757},
        },
        2025: {
            1:  {'US': 5334,  'Amazon_US_FBA': 3435, 'AU': 912,  'CA': 427,  'UK': 726,  'EU': 74},
            2:  {'US': 1157,  'Amazon_US_FBA': 1174, 'AU': 369,  'CA': 158,  'UK': 60,   'EU': 19},
            3:  {'US': 1697,  'Amazon_US_FBA': 1575, 'AU': 497,  'CA': 144,  'UK': 37,   'EU': 25},
            4:  {'US': 2608,  'Amazon_US_FBA': 1735, 'AU': 486,  'CA': 276,  'UK': 214,  'EU': 32},
            5:  {'US': 1141,  'Amazon_US_FBA': 1375, 'AU': 441,  'CA': 222,  'UK': 8,    'EU': 9},
            6:  {'US': 1161,  'Amazon_US_FBA': 1142, 'AU': 496,  'CA': 214,  'UK': 19,   'EU': 10},
            7:  {'US': 939,   'Amazon_US_FBA': 1065, 'AU': 479,  'CA': 201,  'UK': 13,   'EU': 23},
            8:  {'US': 652,   'Amazon_US_FBA': 853,  'AU': 343,  'CA': 75,   'UK': 8,    'EU': 7},
            9:  {'US': 586,   'Amazon_US_FBA': 619,  'AU': 195,  'CA': 97,   'UK': 5,    'EU': 7},
            10: {'US': 853,   'Amazon_US_FBA': 946,  'AU': 683,  'CA': 167,  'UK': 7,    'EU': 12},
            11: {'US': 2293,  'Amazon_US_FBA': 2042, 'AU': 1381, 'CA': 503,  'UK': 2346, 'EU': 569},
            12: {'US': 4019,  'Amazon_US_FBA': 3836, 'AU': 1194, 'CA': 570,  'UK': 1451, 'EU': 625},
        },
        2026: {
            1:  {'US': 724,  'Amazon_US_FBA': 829,  'AU': 379, 'CA': 146, 'UK': 390, 'EU': 69},
            2:  {'US': 296,  'Amazon_US_FBA': 546,  'AU': 305, 'CA': 97,  'UK': 393, 'EU': 79},
        },
    },

    'EIDC2101': {  # Dream Affirmation Cards
        'name': 'Dream Affirmation Cards',
        2024: {
            # Jan-Aug = 0, launched Sep 2024
            9:  {'US': 2103,  'AU': 613,  'CA': 376,  'UK': 669},
            10: {'US': 2157,  'Amazon_US_FBA': 161,  'AU': 716,  'CA': 346,  'UK': 563},
            11: {'US': 1131,  'Amazon_US_FBA': 507,  'AU': 724,  'CA': 284,  'UK': 1238},
            12: {'US': 2854,  'Amazon_US_FBA': 1155, 'AU': 612,  'CA': 233,  'UK': 1794},
        },
        2025: {
            1:  {'US': 846,   'Amazon_US_FBA': 305,  'AU': 250,  'CA': 127,  'UK': 442,  'EU': 86},
            2:  {'US': 362,   'Amazon_US_FBA': 266,  'AU': 255,  'CA': 100,  'UK': 116,  'EU': 60},
            3:  {'US': 352,   'Amazon_US_FBA': 250,  'AU': 193,  'CA': 79,   'UK': 46,   'EU': 38},
            4:  {'US': 1207,  'Amazon_US_FBA': 485,  'AU': 275,  'CA': 270,  'UK': 140,  'EU': 82},
            5:  {'US': 276,   'Amazon_US_FBA': 296,  'AU': 185,  'CA': 119,  'UK': 117,  'EU': 86},
            6:  {'US': 109,   'Amazon_US_FBA': 162,  'AU': 80,   'CA': 28,   'UK': 129,  'EU': 24},
            7:  {'US': 265,   'Amazon_US_FBA': 151,  'AU': 95,   'CA': 23,   'UK': 42,   'EU': 38},
            8:  {'US': 160,   'Amazon_US_FBA': 183,  'AU': 66,   'CA': 33,   'UK': 14,   'EU': 7},
            9:  {'US': 90,    'Amazon_US_FBA': 176,  'AU': 30,   'CA': 19,   'UK': 10,   'EU': 1},
            10: {'US': 165,   'Amazon_US_FBA': 246,  'AU': 97,   'CA': 18,   'UK': 41,   'EU': 17},
            11: {'US': 1599,  'Amazon_US_FBA': 1091, 'AU': 1381, 'CA': 503,  'UK': 2346, 'EU': 569},
            12: {'US': 1682,  'Amazon_US_FBA': 1206, 'AU': 746,  'CA': 341,  'UK': 606,  'EU': 559},
        },
        2026: {
            1:  {'US': 559,  'Amazon_US_FBA': 446,  'AU': 243, 'CA': 117, 'UK': 285, 'EU': 107},
            2:  {'US': 229,  'Amazon_US_FBA': 260,  'AU': 84,  'CA': 66,  'UK': 113, 'EU': 39},
        },
    },

    'EIDJB5002': {  # Know Me If You Can Cards
        'name': 'Know Me Cards',
        2024: {},  # not launched
        2025: {
            # Jan-May = 0, launched Jun 2025
            6:  {'US': 1130,  'AU': 364,  'CA': 187,  'UK': 179,  'EU': 66},
            7:  {'US': 229,   'AU': 157,  'CA': 32,   'UK': 0,    'EU': 13},
            8:  {'US': 551,   'AU': 509,  'CA': 116,  'UK': 9,    'EU': 49},
            9:  {'US': 846,   'Amazon_US_FBA': 48,   'AU': 375,  'CA': 117,  'UK': 2,    'EU': 37},
            10: {'US': 702,   'Amazon_US_FBA': 174,  'AU': 428,  'CA': 95,   'UK': 71,   'EU': 104},
            11: {'US': 5188,  'Amazon_US_FBA': 3594, 'AU': 2490, 'CA': 1136, 'UK': 2439, 'EU': 148},
            12: {'US': 4530,  'Amazon_US_FBA': 4598, 'AU': 1505, 'CA': 747,  'UK': 917,  'EU': 221},
        },
        2026: {
            1:  {'US': 831, 'Amazon_US_FBA': 873, 'AU': 439, 'CA': 161, 'UK': 291, 'EU': 34},
            2:  {'US': 314, 'Amazon_US_FBA': 333, 'AU': 115, 'CA': 97,  'UK': 98,  'EU': 24},
        },
    },
}

MONTH_NAMES = {1:'January',2:'February',3:'March',4:'April',5:'May',6:'June',
               7:'July',8:'August',9:'September',10:'October',11:'November',12:'December'}


def build_rows():
    rows = []
    for sku_id, sku_data in SALES_DATA.items():
        sku_name = sku_data['name']
        for year in [2024, 2025, 2026]:
            year_data = sku_data.get(year, {})
            for month_num in range(1, 13):
                month_data = year_data.get(month_num, {})
                if not month_data:
                    continue
                date = f"{year}-{month_num:02d}-01"
                for warehouse, units in month_data.items():
                    if units and units > 0:
                        rows.append({
                            'date': date,
                            'sku_id': sku_id,
                            'sku_name': sku_name,
                            'warehouse': warehouse,
                            'units_sold': units,
                            'year': year,
                            'month': MONTH_NAMES[month_num],
                        })
    return sorted(rows, key=lambda r: (r['date'], r['sku_id'], r['warehouse']))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    rows = build_rows()
    print(f"Total rows: {len(rows)}")

    # Summary
    from collections import defaultdict
    summary = defaultdict(lambda: defaultdict(int))
    for r in rows:
        summary[r['year']][r['warehouse']] += r['units_sold']

    print("\nUnits by year + warehouse:")
    for yr in sorted(summary):
        for wh, total in sorted(summary[yr].items()):
            print(f"  {yr}  {wh:<20}  {total:>8,}")

    # Expected totals from screenshots for verification
    print("\nExpected 2025 US Shopify by SKU:")
    sku_totals = defaultdict(int)
    for r in rows:
        if r['year'] == 2025 and r['warehouse'] == 'US':
            sku_totals[r['sku_id']] += r['units_sold']
    expected = {'EIDJ2100':12777,'EIDJ4100':23126,'EIDJ5100':8012,'EIDJ5200':4126,
                'EIDJ5000':2941,'EIDC2000':22440,'EIDC2101':7113,'EIDJB5002':13176}
    for sku_id, exp in expected.items():
        got = sku_totals.get(sku_id, 0)
        status = '✓' if got == exp else f'✗ (expected {exp:,})'
        print(f"  {sku_id}: {got:>6,} {status}")

    if args.dry_run:
        print("\n[dry-run] No changes written.")
        return

    service = get_sheets_service()
    sheet_id = get_sheet_id()

    headers = ['Date', 'SKU_ID', 'SKU_Name', 'Warehouse', 'Units_Sold', 'Week_Number', 'Year', 'Notes']
    sheet_rows = [headers] + [
        [r['date'], r['sku_id'], r['sku_name'], r['warehouse'],
         r['units_sold'], '', r['year'], '']
        for r in rows
    ]

    print(f"\nWriting {len(sheet_rows)-1} rows to Sales_Data tab...")
    write_tab(service, sheet_id, 'Sales_Data', sheet_rows)
    print("Done!")


if __name__ == '__main__':
    main()
