
import re, os, subprocess

def info_from_cue(cue):
    infos = cue.split('\nTRACK ')[1:]

    RE_TRACK = re.compile(r'\d+ AUDIO\s*TITLE "([^"]+)".+?(\d+):(\d+):(\d+)', re.S)

    tracks = []
    for info in infos:
        match = RE_TRACK.match(info)
        if not match:
            raise Exception()
        title, minutes, seconds, milliseconds = match.groups()
        # minutes, seconds, milliseconds = int(minutes), int(seconds), int(milliseconds)
        # hours = int(minutes / 60)
        # minutes = minutes % 60
        # print('%02d:%02d:%02d - %s' % (hours, minutes, seconds, title))
        start_seconds = int(minutes) * 60 + int(seconds)
        tracks.append((title, start_seconds))
    return tracks

def info_from_ffprobe(probe):
    infos = probe.split('    Chapter #0:')[1:]

    RE_TRACK = re.compile(r'\d+: start (\d+).+?title\s+:\s+([^\n]+)', re.S)

    tracks = []
    for info in infos:
        match = RE_TRACK.match(info)
        if not match:
            raise Exception()
        start_seconds, title = match.groups()
        tracks.append((title, int(start_seconds)))
    return tracks

# tracks = info_from_cue("""FILE "Angels & Demons.m4b" MP4
# TRACK 1 AUDIO
#   TITLE "Intro"
#   INDEX 01 0:0:00
# TRACK 2 AUDIO
#   TITLE "Preface"
#   INDEX 01 0:41:00
# TRACK 3 AUDIO
#   TITLE "Prologue"
#   INDEX 01 2:30:00
# TRACK 4 AUDIO
#   TITLE "Chapter 1"
#   INDEX 01 3:47:00
# TRACK 5 AUDIO
#   TITLE "Chapter 2"
#   INDEX 01 11:46:00
# TRACK 6 AUDIO
#   TITLE "Chapter 3"
#   INDEX 01 15:5:00
# TRACK 7 AUDIO
#   TITLE "Chapter 4"
#   INDEX 01 16:21:00
# TRACK 8 AUDIO
#   TITLE "Chapter 5"
#   INDEX 01 23:4:00
# TRACK 9 AUDIO
#   TITLE "Chapter 6"
#   INDEX 01 28:13:00
# TRACK 10 AUDIO
#   TITLE "Chapter 7"
#   INDEX 01 35:46:00
# TRACK 11 AUDIO
#   TITLE "Chapter 8"
#   INDEX 01 45:17:00
# TRACK 12 AUDIO
#   TITLE "Chapter 9"
#   INDEX 01 56:28:00
# TRACK 13 AUDIO
#   TITLE "Chapter 10"
#   INDEX 01 67:37:00
# TRACK 14 AUDIO
#   TITLE "Chapter 11"
#   INDEX 01 72:7:00
# TRACK 15 AUDIO
#   TITLE "Chapter 12"
#   INDEX 01 83:25:00
# TRACK 16 AUDIO
#   TITLE "Chapter 13"
#   INDEX 01 84:49:00
# TRACK 17 AUDIO
#   TITLE "Chapter 14"
#   INDEX 01 94:47:00
# TRACK 18 AUDIO
#   TITLE "Chapter 15"
#   INDEX 01 104:6:00
# TRACK 19 AUDIO
#   TITLE "Chapter 16"
#   INDEX 01 113:35:00
# TRACK 20 AUDIO
#   TITLE "Chapter 17"
#   INDEX 01 117:35:00
# TRACK 21 AUDIO
#   TITLE "Chapter 18"
#   INDEX 01 129:58:00
# TRACK 22 AUDIO
#   TITLE "Chapter 19"
#   INDEX 01 132:25:00
# TRACK 23 AUDIO
#   TITLE "Chapter 20"
#   INDEX 01 147:11:00
# TRACK 24 AUDIO
#   TITLE "Chapter 21"
#   INDEX 01 148:50:00
# TRACK 25 AUDIO
#   TITLE "Chapter 22"
#   INDEX 01 158:17:00
# TRACK 26 AUDIO
#   TITLE "Chapter 23"
#   INDEX 01 164:22:00
# TRACK 27 AUDIO
#   TITLE "Chapter 24"
#   INDEX 01 175:32:00
# TRACK 28 AUDIO
#   TITLE "Chapter 25"
#   INDEX 01 177:12:00
# TRACK 29 AUDIO
#   TITLE "Chapter 26"
#   INDEX 01 189:23:00
# TRACK 30 AUDIO
#   TITLE "Chapter 27"
#   INDEX 01 190:56:00
# TRACK 31 AUDIO
#   TITLE "Chapter 28"
#   INDEX 01 199:15:00
# TRACK 32 AUDIO
#   TITLE "Chapter 29"
#   INDEX 01 203:13:00
# TRACK 33 AUDIO
#   TITLE "Chapter 30"
#   INDEX 01 206:45:00
# TRACK 34 AUDIO
#   TITLE "Chapter 31"
#   INDEX 01 211:24:00
# TRACK 35 AUDIO
#   TITLE "Chapter 32"
#   INDEX 01 224:13:00
# TRACK 36 AUDIO
#   TITLE "Chapter 33"
#   INDEX 01 233:12:00
# TRACK 37 AUDIO
#   TITLE "Chapter 34"
#   INDEX 01 239:50:00
# TRACK 38 AUDIO
#   TITLE "Chapter 35"
#   INDEX 01 243:59:00
# TRACK 39 AUDIO
#   TITLE "Chapter 36"
#   INDEX 01 251:1:00
# TRACK 40 AUDIO
#   TITLE "Chapter 37"
#   INDEX 01 269:57:00
# TRACK 41 AUDIO
#   TITLE "Chapter 38"
#   INDEX 01 275:17:00
# TRACK 42 AUDIO
#   TITLE "Chapter 39"
#   INDEX 01 280:56:00
# TRACK 43 AUDIO
#   TITLE "Chapter 40"
#   INDEX 01 290:0:00
# TRACK 44 AUDIO
#   TITLE "Chapter 41"
#   INDEX 01 298:3:00
# TRACK 45 AUDIO
#   TITLE "Chapter 42"
#   INDEX 01 317:15:00
# TRACK 46 AUDIO
#   TITLE "Chapter 43"
#   INDEX 01 324:56:00
# TRACK 47 AUDIO
#   TITLE "Chapter 44"
#   INDEX 01 336:42:00
# TRACK 48 AUDIO
#   TITLE "Chapter 45"
#   INDEX 01 339:49:00
# TRACK 49 AUDIO
#   TITLE "Chapter 46"
#   INDEX 01 350:45:00
# TRACK 50 AUDIO
#   TITLE "Chapter 47"
#   INDEX 01 364:40:00
# TRACK 51 AUDIO
#   TITLE "Chapter 48"
#   INDEX 01 375:6:00
# TRACK 52 AUDIO
#   TITLE "Chapter 49"
#   INDEX 01 379:23:00
# TRACK 53 AUDIO
#   TITLE "Chapter 50"
#   INDEX 01 400:31:00
# TRACK 54 AUDIO
#   TITLE "Chapter 51"
#   INDEX 01 406:38:00
# TRACK 55 AUDIO
#   TITLE "Chapter 52"
#   INDEX 01 409:33:00
# TRACK 56 AUDIO
#   TITLE "Chapter 53"
#   INDEX 01 420:30:00
# TRACK 57 AUDIO
#   TITLE "Chapter 54"
#   INDEX 01 421:52:00
# TRACK 58 AUDIO
#   TITLE "Chapter 55"
#   INDEX 01 433:11:00
# TRACK 59 AUDIO
#   TITLE "Chapter 56"
#   INDEX 01 445:30:00
# TRACK 60 AUDIO
#   TITLE "Chapter 57"
#   INDEX 01 453:44:00
# TRACK 61 AUDIO
#   TITLE "Chapter 58"
#   INDEX 01 454:55:00
# TRACK 62 AUDIO
#   TITLE "Chapter 59"
#   INDEX 01 462:46:00
# TRACK 63 AUDIO
#   TITLE "Chapter 60"
#   INDEX 01 465:51:00
# TRACK 64 AUDIO
#   TITLE "Chapter 61"
#   INDEX 01 470:11:00
# TRACK 65 AUDIO
#   TITLE "Chapter 62"
#   INDEX 01 483:58:00
# TRACK 66 AUDIO
#   TITLE "Chapter 63"
#   INDEX 01 497:53:00
# TRACK 67 AUDIO
#   TITLE "Chapter 64"
#   INDEX 01 504:19:00
# TRACK 68 AUDIO
#   TITLE "Chapter 65"
#   INDEX 01 513:52:00
# TRACK 69 AUDIO
#   TITLE "Chapter 66"
#   INDEX 01 531:13:00
# TRACK 70 AUDIO
#   TITLE "Chapter 67"
#   INDEX 01 534:37:00
# TRACK 71 AUDIO
#   TITLE "Chapter 68"
#   INDEX 01 541:6:00
# TRACK 72 AUDIO
#   TITLE "Chapter 69"
#   INDEX 01 546:48:00
# TRACK 73 AUDIO
#   TITLE "Chapter 70"
#   INDEX 01 558:52:00
# TRACK 74 AUDIO
#   TITLE "Chapter 71"
#   INDEX 01 565:35:00
# TRACK 75 AUDIO
#   TITLE "Chapter 72"
#   INDEX 01 570:32:00
# TRACK 76 AUDIO
#   TITLE "Chapter 73"
#   INDEX 01 576:44:00
# TRACK 77 AUDIO
#   TITLE "Chapter 74"
#   INDEX 01 585:13:00
# TRACK 78 AUDIO
#   TITLE "Chapter 75"
#   INDEX 01 589:0:00
# TRACK 79 AUDIO
#   TITLE "Chapter 76"
#   INDEX 01 592:34:00
# TRACK 80 AUDIO
#   TITLE "Chapter 77"
#   INDEX 01 596:16:00
# TRACK 81 AUDIO
#   TITLE "Chapter 78"
#   INDEX 01 598:33:00
# TRACK 82 AUDIO
#   TITLE "Chapter 79"
#   INDEX 01 600:49:00
# TRACK 83 AUDIO
#   TITLE "Chapter 80"
#   INDEX 01 612:50:00
# TRACK 84 AUDIO
#   TITLE "Chapter 81"
#   INDEX 01 616:38:00
# TRACK 85 AUDIO
#   TITLE "Chapter 82"
#   INDEX 01 634:59:00
# TRACK 86 AUDIO
#   TITLE "Chapter 83"
#   INDEX 01 640:22:00
# TRACK 87 AUDIO
#   TITLE "Chapter 84"
#   INDEX 01 648:28:00
# TRACK 88 AUDIO
#   TITLE "Chapter 85"
#   INDEX 01 658:46:00
# TRACK 89 AUDIO
#   TITLE "Chapter 86"
#   INDEX 01 666:13:00
# TRACK 90 AUDIO
#   TITLE "Chapter 87"
#   INDEX 01 677:22:00
# TRACK 91 AUDIO
#   TITLE "Chapter 88"
#   INDEX 01 682:30:00
# TRACK 92 AUDIO
#   TITLE "Chapter 89"
#   INDEX 01 692:44:00
# TRACK 93 AUDIO
#   TITLE "Chapter 90"
#   INDEX 01 702:22:00
# TRACK 94 AUDIO
#   TITLE "Chapter 91"
#   INDEX 01 709:49:00
# TRACK 95 AUDIO
#   TITLE "Chapter 92"
#   INDEX 01 719:58:00
# TRACK 96 AUDIO
#   TITLE "Chapter 93"
#   INDEX 01 721:38:00
# TRACK 97 AUDIO
#   TITLE "Chapter 94"
#   INDEX 01 730:53:00
# TRACK 98 AUDIO
#   TITLE "Chapter 95"
#   INDEX 01 746:20:00
# TRACK 99 AUDIO
#   TITLE "Chapter 96"
#   INDEX 01 749:52:00
# TRACK 100 AUDIO
#   TITLE "Chapter 97"
#   INDEX 01 758:56:00
# TRACK 101 AUDIO
#   TITLE "Chapter 98"
#   INDEX 01 762:42:00
# TRACK 102 AUDIO
#   TITLE "Chapter 99"
#   INDEX 01 765:48:00
# TRACK 103 AUDIO
#   TITLE "Chapter 100"
#   INDEX 01 769:49:00
# TRACK 104 AUDIO
#   TITLE "Chapter 101"
#   INDEX 01 786:55:00
# TRACK 105 AUDIO
#   TITLE "Chapter 102"
#   INDEX 01 794:1:00
# TRACK 106 AUDIO
#   TITLE "Chapter 103"
#   INDEX 01 807:21:00
# TRACK 107 AUDIO
#   TITLE "Chapter 104"
#   INDEX 01 815:38:00
# TRACK 108 AUDIO
#   TITLE "Chapter 105"
#   INDEX 01 819:9:00
# TRACK 109 AUDIO
#   TITLE "Chapter 106"
#   INDEX 01 827:49:00
# TRACK 110 AUDIO
#   TITLE "Chapter 107"
#   INDEX 01 837:0:00
# TRACK 111 AUDIO
#   TITLE "Chapter 108"
#   INDEX 01 851:29:00
# TRACK 112 AUDIO
#   TITLE "Chapter 109"
#   INDEX 01 868:51:00
# TRACK 113 AUDIO
#   TITLE "Chapter 110"
#   INDEX 01 871:53:00
# TRACK 114 AUDIO
#   TITLE "Chapter 111"
#   INDEX 01 877:15:00
# TRACK 115 AUDIO
#   TITLE "Chapter 112"
#   INDEX 01 887:0:00
# TRACK 116 AUDIO
#   TITLE "Chapter 113"
#   INDEX 01 896:10:00
# TRACK 117 AUDIO
#   TITLE "Chapter 114"
#   INDEX 01 904:47:00
# TRACK 118 AUDIO
#   TITLE "Chapter 115"
#   INDEX 01 911:38:00
# TRACK 119 AUDIO
#   TITLE "Chapter 116"
#   INDEX 01 914:56:00
# TRACK 120 AUDIO
#   TITLE "Chapter 117"
#   INDEX 01 920:17:00
# TRACK 121 AUDIO
#   TITLE "Chapter 118"
#   INDEX 01 924:29:00
# TRACK 122 AUDIO
#   TITLE "Chapter 119"
#   INDEX 01 936:58:00
# TRACK 123 AUDIO
#   TITLE "Chapter 120"
#   INDEX 01 946:43:00
# TRACK 124 AUDIO
#   TITLE "Chapter 121"
#   INDEX 01 956:5:00
# TRACK 125 AUDIO
#   TITLE "Chapter 122"
#   INDEX 01 963:9:00
# TRACK 126 AUDIO
#   TITLE "Chapter 123"
#   INDEX 01 967:22:00
# TRACK 127 AUDIO
#   TITLE "Chapter 124"
#   INDEX 01 971:40:00
# TRACK 128 AUDIO
#   TITLE "Chapter 125"
#   INDEX 01 976:12:00
# TRACK 129 AUDIO
#   TITLE "Chapter 126"
#   INDEX 01 988:57:00
# TRACK 130 AUDIO
#   TITLE "Chapter 127"
#   INDEX 01 992:38:00
# TRACK 131 AUDIO
#   TITLE "Chapter 128"
#   INDEX 01 1002:57:00
# TRACK 132 AUDIO
#   TITLE "Chapter 129"
#   INDEX 01 1010:13:00
# TRACK 133 AUDIO
#   TITLE "Chapter 130"
#   INDEX 01 1027:9:00
# TRACK 134 AUDIO
#   TITLE "Chapter 131"
#   INDEX 01 1033:14:00
# TRACK 135 AUDIO
#   TITLE "Chapter 132"
#   INDEX 01 1052:46:00
# TRACK 136 AUDIO
#   TITLE "Chapter 133"
#   INDEX 01 1055:18:00
# TRACK 137 AUDIO
#   TITLE "Chapter 134"
#   INDEX 01 1068:59:00
# TRACK 138 AUDIO
#   TITLE "Chapter 135"
#   INDEX 01 1083:24:00
# TRACK 139 AUDIO
#   TITLE "Chapter 136"
#   INDEX 01 1087:27:00
# TRACK 140 AUDIO
#   TITLE "Chapter 137"
#   INDEX 01 1098:2:00
# TRACK 141 AUDIO
#   TITLE "Outro"
#   INDEX 01 1109:51:00
# """)
tracks = info_from_ffprobe("""    Chapter #0:0: start 2.000000, end 1054.604000
      Metadata:
        title           : Intro
    Chapter #0:0: start 12.000000, end 1054.604000
      Metadata:
        title           : Preface
    Chapter #0:0: start 45.000000, end 1054.604000
      Metadata:
        title           : Prologue
    Chapter #0:1: start 1054.604000, end 2103.867000
      Metadata:
        title           : Chapter 1
    Chapter #0:2: start 2103.867000, end 3063.548000
      Metadata:
        title           : Chapter 2
    Chapter #0:3: start 3063.548000, end 3914.950000
      Metadata:
        title           : Chapter 3
    Chapter #0:4: start 3914.950000, end 3977.680000
      Metadata:
        title           : Chapter 4
    Chapter #0:5: start 3977.680000, end 4780.711000
      Metadata:
        title           : Chapter 5
    Chapter #0:6: start 4780.711000, end 5615.793000
      Metadata:
        title           : Chapter 6
    Chapter #0:7: start 5615.793000, end 5873.209000
      Metadata:
        title           : Chapter 7
    Chapter #0:8: start 5873.209000, end 7117.799000
      Metadata:
        title           : Chapter 8
    Chapter #0:9: start 7117.799000, end 8132.000000
      Metadata:
        title           : Chapter 9
    Chapter #0:10: start 8132.000000, end 8746.261000
      Metadata:
        title           : Chapter 10
    Chapter #0:11: start 8746.261000, end 8846.200000
      Metadata:
        title           : Chapter 11
    Chapter #0:12: start 8846.200000, end 9396.200000
      Metadata:
        title           : Chapter 12
    Chapter #0:13: start 9396.200000, end 9576.235000
      Metadata:
        title           : Chapter 13
    Chapter #0:14: start 9576.235000, end 10249.521000
      Metadata:
        title           : Chapter 14
    Chapter #0:15: start 10249.521000, end 10697.713000
      Metadata:
        title           : Chapter 15
    Chapter #0:16: start 10697.713000, end 11056.136000
      Metadata:
        title           : Chapter 16
    Chapter #0:17: start 11056.136000, end 12578.761000
      Metadata:
        title           : Chapter 17
    Chapter #0:18: start 12578.761000, end 12637.461000
      Metadata:
        title           : Chapter 18
    Chapter #0:19: start 12637.461000, end 13059.135000
      Metadata:
        title           : Chapter 19
    Chapter #0:20: start 13059.135000, end 14101.990000
      Metadata:
        title           : Chapter 20
    Chapter #0:21: start 14101.990000, end 14750.198000
      Metadata:
        title           : Chapter 21
    Chapter #0:22: start 14750.198000, end 15195.920000
      Metadata:
        title           : Chapter 22
    Chapter #0:23: start 15195.920000, end 15935.112000
      Metadata:
        title           : Chapter 23
    Chapter #0:24: start 15935.112000, end 16633.429000
      Metadata:
        title           : Chapter 24
    Chapter #0:25: start 16633.429000, end 17071.172000
      Metadata:
        title           : Chapter 25
    Chapter #0:26: start 17071.172000, end 17563.640000
      Metadata:
        title           : Chapter 26
    Chapter #0:27: start 17563.640000, end 18211.504000
      Metadata:
        title           : Chapter 27
    Chapter #0:28: start 18211.504000, end 18962.995000
      Metadata:
        title           : Chapter 28
    Chapter #0:29: start 18962.995000, end 19151.402000
      Metadata:
        title           : Chapter 29
    Chapter #0:30: start 19151.402000, end 19810.709000
      Metadata:
        title           : Chapter 30
    Chapter #0:31: start 19810.709000, end 20175.123000
      Metadata:
        title           : Chapter 31
    Chapter #0:32: start 20175.123000, end 20738.903000
      Metadata:
        title           : Chapter 32
    Chapter #0:33: start 20738.903000, end 21623.723000
      Metadata:
        title           : Chapter 33
    Chapter #0:34: start 21623.723000, end 21682.887000
      Metadata:
        title           : Chapter 34
    Chapter #0:35: start 21682.887000, end 22644.193000
      Metadata:
        title           : Chapter 35
    Chapter #0:36: start 22644.193000, end 23455.545000
      Metadata:
        title           : Chapter 36
    Chapter #0:37: start 23455.545000, end 24188.274000
      Metadata:
        title           : Chapter 37
    Chapter #0:38: start 24188.274000, end 24480.567000
      Metadata:
        title           : Chapter 38
    Chapter #0:39: start 24480.567000, end 25099.540000
      Metadata:
        title           : Chapter 39
    Chapter #0:40: start 25099.540000, end 25578.871000
      Metadata:
        title           : Chapter 40
    Chapter #0:41: start 25578.871000, end 26037.140000
      Metadata:
        title           : Chapter 41
    Chapter #0:42: start 26037.140000, end 26773.956000
      Metadata:
        title           : Chapter 42
    Chapter #0:43: start 26773.956000, end 27561.112000
      Metadata:
        title           : Chapter 43
    Chapter #0:44: start 27561.112000, end 28747.652000
      Metadata:
        title           : Chapter 44
    Chapter #0:45: start 28747.652000, end 29441.604000
      Metadata:
        title           : Chapter 45
    Chapter #0:46: start 29441.604000, end 29478.524000
      Metadata:
        title           : Chapter 46
    Chapter #0:47: start 29478.524000, end 30055.493000
      Metadata:
        title           : Chapter 47
    Chapter #0:48: start 30055.493000, end 30938.594000
      Metadata:
        title           : Chapter 48
    Chapter #0:49: start 30938.594000, end 31855.922000
      Metadata:
        title           : Chapter 49
    Chapter #0:50: start 31855.922000, end 32673.357000
      Metadata:
        title           : Chapter 50
    Chapter #0:51: start 32673.357000, end 33548.703000
      Metadata:
        title           : Chapter 51
    Chapter #0:52: start 33548.703000, end 34730.924000
      Metadata:
        title           : Chapter 52
    Chapter #0:53: start 34730.924000, end 35481.114000
      Metadata:
        title           : Chapter 53
    Chapter #0:54: start 35481.114000, end 35788.918000
      Metadata:
        title           : Chapter 54
    Chapter #0:55: start 35788.918000, end 36499.310000
      Metadata:
        title           : Chapter 55
    Chapter #0:56: start 36499.310000, end 36842.361000
      Metadata:
        title           : Chapter 56
    Chapter #0:57: start 36842.361000, end 37877.228000
      Metadata:
        title           : Chapter 57
    Chapter #0:58: start 37877.228000, end 37937.414000
      Metadata:
        title           : Chapter 58
    Chapter #0:59: start 37937.414000, end 38703.255000
      Metadata:
        title           : Chapter 59
    Chapter #0:60: start 38703.255000, end 39370.782000
      Metadata:
        title           : Chapter 60
    Chapter #0:61: start 39370.782000, end 40277.243000
      Metadata:
        title           : Chapter 61
    Chapter #0:62: start 40277.243000, end 40416.563000
      Metadata:
        title           : Chapter 62
    Chapter #0:63: start 40416.563000, end 41243.101000
      Metadata:
        title           : Chapter 63
    Chapter #0:64: start 41243.101000, end 41881.603000
      Metadata:
        title           : Chapter 64
    Chapter #0:65: start 41881.603000, end 42685.130000
      Metadata:
        title           : Chapter 65
    Chapter #0:66: start 42685.130000, end 43140.589000
      Metadata:
        title           : Chapter 66
    Chapter #0:67: start 43140.589000, end 43480.650000
      Metadata:
        title           : Chapter 67
    Chapter #0:68: start 43480.650000, end 43653.147000
      Metadata:
        title           : Chapter 68
    Chapter #0:69: start 43653.147000, end 44366.743000
      Metadata:
        title           : Chapter 69
    Chapter #0:70: start 44366.743000, end 45203.404000
      Metadata:
        title           : Chapter 70
    Chapter #0:71: start 45203.404000, end 45289.411000
      Metadata:
        title           : Chapter 71
    Chapter #0:72: start 45289.411000, end 46197.822000
      Metadata:
        title           : Chapter 72
    Chapter #0:73: start 46197.822000, end 46782.175000
      Metadata:
        title           : Chapter 73
    Chapter #0:74: start 46782.175000, end 47310.429000
      Metadata:
        title           : Chapter 74
    Chapter #0:75: start 47310.429000, end 48217.290000
      Metadata:
        title           : Chapter 75
    Chapter #0:76: start 48217.290000, end 48464.890000
      Metadata:
        title           : Chapter 76
    Chapter #0:77: start 48464.890000, end 49086.848000
      Metadata:
        title           : Chapter 77
    Chapter #0:78: start 49086.848000, end 49144.155000
      Metadata:
        title           : Chapter 78
    Chapter #0:79: start 49144.155000, end 49382.438000
      Metadata:
        title           : Chapter 79
    Chapter #0:80: start 49382.438000, end 50359.859000
      Metadata:
        title           : Chapter 80
    Chapter #0:81: start 50359.859000, end 50593.730000
      Metadata:
        title           : Chapter 81
    Chapter #0:82: start 50593.730000, end 50666.919000
      Metadata:
        title           : Chapter 82
    Chapter #0:83: start 50666.919000, end 51162.665000
      Metadata:
        title           : Chapter 83
    Chapter #0:84: start 51162.665000, end 51924.140000
      Metadata:
        title           : Chapter 84
    Chapter #0:85: start 51924.140000, end 51998.537000
      Metadata:
        title           : Chapter 85
    Chapter #0:86: start 51998.537000, end 52412.840000
      Metadata:
        title           : Chapter 86
    Chapter #0:87: start 52412.840000, end 53353.189000
      Metadata:
        title           : Chapter 87
    Chapter #0:88: start 53353.189000, end 54015.933000
      Metadata:
        title           : Chapter 88
    Chapter #0:89: start 54015.933000, end 54055.453000
      Metadata:
        title           : Chapter 89
    Chapter #0:90: start 54055.453000, end 54658.940000
      Metadata:
        title           : Chapter 90
    Chapter #0:91: start 54658.940000, end 55881.146000
      Metadata:
        title           : Chapter 91
    Chapter #0:92: start 55881.146000, end 56460.190000
      Metadata:
        title           : Chapter 92
    Chapter #0:93: start 56460.190000, end 57264.916000
      Metadata:
        title           : Chapter 93
    Chapter #0:94: start 57264.916000, end 57366.434000
      Metadata:
        title           : Chapter 94
    Chapter #0:95: start 57366.434000, end 58265.460000
      Metadata:
        title           : Chapter 95
    Chapter #0:96: start 58265.460000, end 59182.606000
      Metadata:
        title           : Chapter 96
    Chapter #0:97: start 59182.606000, end 59797.192000
      Metadata:
        title           : Chapter 97
    Chapter #0:98: start 59797.192000, end 60961.580000
      Metadata:
        title           : Chapter 98
    Chapter #0:99: start 60961.580000, end 61686.553000
      Metadata:
        title           : Chapter 99
    Chapter #0:100: start 61686.553000, end 61945.316000
      Metadata:
        title           : Chapter 100
    Chapter #0:101: start 61945.316000, end 62084.729000
      Metadata:
        title           : Chapter 101
    Chapter #0:102: start 62084.729000, end 62800.647000
      Metadata:
        title           : Chapter 102
    Chapter #0:103: start 62800.647000, end 63161.206000
      Metadata:
        title           : Chapter 103
    Chapter #0:104: start 63161.206000, end 64016.908000
      Metadata:
        title           : Chapter 104
    Chapter #0:105: start 64016.908000, end 64719.172000
      Metadata:
        title           : Chapter 105
    Chapter #0:106: start 64719.172000, end 65444.490000
      Metadata:
        title           : Epilogue""")

audiobook = '/Users/zachzahos/Documents/Audiobooks/Robert Langdon #5 - Origin/Origin.m4b'
output_dir = '/Users/zachzahos/Documents/Audiobooks/Robert Langdon/Origin'

for n, ((title, start), (_, end)) in enumerate(zip(tracks, tracks[1:] + [(None, None)]), 1):
    command = ['ffmpeg', '-ss', '%d' % start, '-i', audiobook, '-vn', '-c:a', 'libmp3lame', '-q:a', '0']
    if end != None:
        command.extend(['-to', '%d' % (end - start)])
    command.append(os.path.join(output_dir, '%03d - %s.mp3' % (n, title)))
    print(' '.join(command))
    print(subprocess.run(command))
    # if n == 3:
    #     break
