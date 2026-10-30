# -*- coding: utf-8 -*-
"""Dữ liệu phiên bản 0.3: mục đích, case study theo mục đích, bước xử lý của yếu tố, câu của người dùng, khung câu, đánh giá."""
import sys
sys.path.insert(0, ".")
import data_def as D
import taxonomy_def as TX

# ------------------------------------------------------------------ bước xử lý
S_TEXT = "1. Thiết kế câu (văn bản)"
S_VOICE = "2. Chọn giọng và đoạn tham chiếu"
S_CTL = "3. Điều khiển khi sinh TTS"
S_MIX = "4. Trộn nhiễu và mô phỏng khoang xe (sau TTS)"
S_DSP = "5. Chuỗi xử lý đầu vào (sau trộn)"
S_EVAL = "6. Chỉ để đánh giá"
S_FT = "Tinh chỉnh TTS (tùy chọn)"
S_OUT = "Ngoài phạm vi ASR (phía loa hoặc hệ thống)"
STAGES = [S_TEXT, S_VOICE, S_CTL, S_MIX, S_DSP, S_EVAL, S_FT, S_OUT]

STAGE_DESC = {
    S_TEXT: "Quyết định bằng chính câu: mẫu câu, khe thông tin, từ vựng vùng, số, tên riêng, độ dài. Đây là phần bộ mẫu câu phải đáp ứng trực tiếp.",
    S_VOICE: "Quyết định bằng người nói được clone: vùng, giới, F0, chất giọng. Xử lý bằng hạn ngạch người nói và chọn đoạn tham chiếu, không bằng câu.",
    S_CTL: "Điều khiển lúc sinh âm thanh: tốc độ, phong cách, ngắt nghỉ, cảm xúc. Kết quả phải đo lại sau khi sinh.",
    S_MIX: "Thêm sau khi TTS đã sinh âm thanh sạch: tiếng ồn, vang khoang xe, mức giọng so với ồn, vị trí mic.",
    S_DSP: "Chuỗi xử lý giữa mic và bộ nhận dạng: tần số lấy mẫu, codec, khử ồn, AGC. Dùng cùng chuỗi khi tạo dữ liệu và khi chạy thật.",
    S_EVAL: "Không điều khiển được khi sinh; chỉ có thể đo ở bộ đánh giá.",
    S_FT: "Nếu zero-shot không giữ được giọng vùng thì tinh chỉnh TTS trên giọng thật có nhãn vùng.",
    S_OUT: "Thuộc đường phát ra loa hoặc hệ thống trợ lý, không ảnh hưởng dữ liệu huấn luyện ASR; giữ lại cho giai đoạn đánh giá TTS sản phẩm (mục đích M5).",
}

STAGE = {}
for c in ["A01", "A02", "A03", "A04", "A05", "A06", "A07", "A08", "A09", "A10", "A12", "A13", "B01"]:
    STAGE[c] = (S_MIX, "")
STAGE["A11"] = (S_MIX, S_EVAL)
STAGE["A14"] = (S_MIX, S_VOICE)
STAGE["B05"] = (S_DSP, S_OUT)
STAGE["B07"] = (S_MIX, S_DSP)
STAGE["B10"] = (S_EVAL, S_MIX)
for c in ["B02", "B03", "B04", "B06", "B08", "B09", "C04", "C05", "C06", "C08", "D02", "D04", "D05"]:
    STAGE[c] = (S_OUT, "")
for c in ["C01", "C02", "C03", "C07", "C09"]:
    STAGE[c] = (S_DSP, "")
STAGE["D01"] = (S_TEXT, S_CTL)
STAGE["D03"] = (S_TEXT, S_CTL)
STAGE["E02"] = (S_TEXT, S_EVAL)
for c in ["E03", "E04", "E05", "E06", "E07", "E08", "S51", "S52", "S53", "S54", "S55"]:
    STAGE[c] = (S_TEXT, "")
for c in ["S11", "S12", "S13", "S15", "S16", "S25", "S42", "S45"]:
    STAGE[c] = (S_VOICE, "")
STAGE["S14"] = (S_CTL, S_VOICE)
STAGE["S21"] = (S_CTL, S_VOICE)
STAGE["S22"] = (S_CTL, "")
STAGE["S23"] = (S_TEXT, S_CTL)
STAGE["S24"] = (S_CTL, S_MIX)
STAGE["S31"] = (S_CTL, "")
STAGE["S32"] = (S_MIX, "")
STAGE["S33"] = (S_CTL, S_TEXT)
STAGE["S34"] = (S_CTL, S_TEXT)
STAGE["S35"] = (S_MIX, "")
STAGE["S41"] = (S_VOICE, S_FT)
STAGE["S43"] = (S_VOICE, S_EVAL)
STAGE["S44"] = (S_VOICE, S_EVAL)

ACTION_DEFAULT = {
    S_TEXT: "Phủ bằng mẫu câu × khe (sheet Mau_khung) và câu mẫu (Mau_cau); kiểm bằng cột factors_covered và ma trận Ma_tran.",
    S_VOICE: "Đặt hạn ngạch người nói ở Chi_tieu; chọn đoạn tham chiếu theo hồ sơ ở Ho_so_nguoi_noi.",
    S_CTL: "Điều khiển khi sinh (tốc độ, phong cách, tham chiếu) rồi đo lại bằng căn chỉnh hoặc nghe kiểm.",
    S_MIX: "Trộn sau khi có âm thanh sạch; ghi nguồn ồn và snr_actual_dB; dùng nhiều nguồn ồn và ồn đổi giữa câu.",
    S_DSP: "Áp cùng chuỗi xử lý khi tạo dữ liệu và khi chạy thật.",
    S_EVAL: "Đưa vào bộ đánh giá; không dùng làm điều khiển khi sinh.",
    S_FT: "",
    S_OUT: "Không đưa vào dữ liệu ASR; giữ cho đánh giá TTS sản phẩm (M5).",
}
ACTION_SPECIFIC = {
    "S12": "Trẻ em và người cao tuổi: cần nguồn giọng thật có đồng ý. Không tạo từ giọng người lớn bằng dịch cao độ (nhận định của mình, chưa kiểm chứng); nếu không có nguồn thì để ngoài phạm vi.",
    "S13": "Chọn người nói có F0 tự nhiên khác nhau; không dịch cao độ để tăng độ phủ F0.",
    "S24": "Chưa có cách đã kiểm chứng. Nếu mô phỏng thì gắn nhãn lombard_applied = Mô phỏng; ưu tiên thu thật một tập nhỏ nếu làm được.",
    "S41": "Đoạn tham chiếu cùng vùng với nhãn câu; tách Bắc Trung Bộ và Nam Trung Bộ; kiểm bằng bộ phân loại và người bản ngữ; nếu giọng bị kéo về giọng chuẩn thì tinh chỉnh theo vùng.",
    "S43": "Dùng cặp câu tối thiểu hỏi/ngã trong tập chẩn đoán M4 và nghe kiểm theo vùng.",
    "S44": "Dùng tên đường, địa danh có tr/ch, s/x, r/d/gi trong M4; người bản ngữ rà.",
    "S51": "Mỗi ý định có biến thể Bắc, Trung, Nam trong Mau_khung; từ vựng lấy từ Tu_dia_phuong và do người bản ngữ duyệt.",
    "S53": "Chuẩn hóa số theo vùng (lẻ/linh, nghìn/ngàn); có cặp câu M4 cho từng cách đọc.",
    "A14": "Cần giọng thứ hai: lấy từ cùng kho giọng clone, trộn ở nhiều mức chồng lấn.",
    "E02": "Cặp câu tối thiểu thanh hỏi/ngã, sắc/nặng trong M4; đo ở bộ đánh giá có nhiễu.",
    "E08": "Mỗi case có cả câu rất ngắn (1–3 âm tiết) và câu thường; theo dõi cột do_dai ở Mau_cau.",
    "S31": "Điều khiển tốc độ bằng tham số của mô hình TTS; đo lại âm tiết mỗi giây.",
}

EV_NOISE = "Trộn nhiễu giảm WER khoảng 5,1%, nhiễu cộng vang khoảng 6,6% (Ogun et al. 2025; Common Voice tiếng Anh, 50 giờ thật; cần kiểm chứng cho tiếng Việt)."
EV_TEXT = "Đa dạng câu quan trọng hơn đa dạng người nói; dưới khoảng 10.000 câu thì CER tăng rõ (Versatile TTS, Mân Nam; chưa kiểm chứng cho tiếng Việt)."
EV_SPK = "Thêm người nói chỉ giảm WER khoảng 2%; khoảng 50–100 người nói là đủ (Ogun et al.; Versatile TTS)."
EV_ACC = "Zero-shot giữ giọng người nói nhưng kéo giọng vùng về giọng chuẩn; tinh chỉnh cải thiện độ giống giọng vùng (Singlish, tiếng Anh; chưa có cho tiếng Việt)."
EVID = {}
for c in ["A01", "A02", "A03", "A04", "A05", "A06", "A07", "A08", "A09", "A10", "A11", "A12", "B01", "B07"]:
    EVID[c] = EV_NOISE
for c in ["E03", "E04", "E05", "E06", "E07", "E08", "S51", "S52", "S53", "S54", "S55"]:
    EVID[c] = EV_TEXT
for c in ["S11", "S12", "S14", "S15", "S16", "S25"]:
    EVID[c] = EV_SPK
EVID["S13"] = "Dịch cao độ và đổi giọng để tăng đa dạng người nói không hiệu quả (Ogun et al.: WER tệ hơn 0,8% và 2,2%)."
for c in ["S41", "S42", "S43", "S44", "S45"]:
    EVID[c] = EV_ACC
EVID["S24"] = "Có paper TTS mô phỏng hiệu ứng Lombard nhưng mới đọc phần tóm tắt, chưa có số liệu ASR (Akti và Waibel 2026)."
EVID["S33"] = "Chưa có bằng chứng đã đọc."
EVID["S34"] = "Chưa có bằng chứng đã đọc."


def factor_rows():
    rows = []
    for x in TX.full_table():
        g, sub, code, name, level, side, impact, how, metric, prio, fld, sol, real, ver = x
        p, q = STAGE[code]
        act = ACTION_SPECIFIC.get(code, ACTION_DEFAULT[p])
        ev = EVID.get(code, "Chưa có bằng chứng đã đọc.")
        rows.append([g, sub, code, name, level, side, p, q, act, ev, impact, metric, prio, real])
    return rows


# ------------------------------------------------------------------ mục đích dữ liệu
# (mã, tên, ai nói, dùng để làm gì, vào huấn luyện ASR, vào kiểm thử, nguồn văn bản, nguồn giọng, bước áp dụng, ghi chú)
PURPOSES = [
    ("M1", "Lệnh và câu hỏi của người dùng trong xe (sinh)", "Người dùng",
     "Dữ liệu chính cần sinh: những gì người lái hoặc hành khách nói với trợ lý. Đây là thứ ASR phải nhận ra.",
     "Có", "Một phần giữ lại, chia theo người nói và mẫu câu",
     "Mẫu câu × khe + diễn đạt lại bằng LLM, người bản ngữ duyệt (xem Mau_khung)",
     "Clone từ giọng thật có nhãn vùng; đoạn tham chiếu cùng vùng với từ vựng của câu",
     "Bước 1 đến 5 (mọi yếu tố phía người nói và nhiễu)",
     "Phần lớn số câu nằm ở đây. Chưa có paper đo trên tiếng Việt."),
    ("M2", "Câu trả lời ngắn cho trợ lý (sinh)", "Người dùng",
     "Câu 1 đến 3 âm tiết đáp lại câu hỏi của hệ thống: có, không, cái thứ hai, hủy, một con số.",
     "Có", "Một phần giữ lại",
     "Danh sách câu trả lời theo từng loại câu hỏi của hệ thống",
     "Như M1",
     "Bước 1 đến 5",
     "Câu rất ngắn là điểm TTS dễ lỗi (PhoAudiobook: XTTS-v2 WER 37,81% trên VIVOS); cần theo dõi riêng."),
    ("M3", "Tập đối chiếu ngoài miền xe (sinh)", "Người đọc",
     "Cùng giọng, cùng quy trình sinh và trộn nhiễu như M1 nhưng câu lấy từ tập thật ngoài miền xe. Dùng để tách ảnh hưởng của 'giọng sinh' khỏi ảnh hưởng của 'miền xe', và tránh việc ASR học 'âm thanh kiểu TTS là lệnh xe'.",
     "Có", "Không",
     "Transcript của bộ thật ngoài miền xe (chưa chọn; kiểm giấy phép từng bộ)",
     "Clone từ cùng kho giọng như M1",
     "Bước 2 đến 5",
     "Đề xuất của mình, chưa paper nào kiểm riêng thiết kế này. Không dùng câu của tập kiểm thử."),
    ("M4", "Câu chẩn đoán để chọn mô hình TTS", "Người đọc",
     "Bộ nhỏ chạy trên các mô hình TTS chưa tinh chỉnh để so sánh: câu rất ngắn, số, tên riêng, cặp thanh điệu, từ vùng, chuyển mã.",
     "Không", "Có (đánh giá TTS)",
     "Viết tay, cố định",
     "Một vài giọng mỗi vùng",
     "Chỉ dùng ở bước chọn mô hình",
     "Đo WER hai ASR, độ giống người nói, độ giống giọng vùng, nghe bản ngữ."),
    ("M5", "Lời trợ lý phát ra loa trong xe", "Trợ lý",
     "Câu dẫn đường, cảnh báo, xác nhận mà trợ lý nói (47 câu mẫu của bảng v0.2 thuộc loại này).",
     "Không", "Không (ngoài phạm vi ASR)",
     "Bảng v0.2 (Mau_du_lieu cũ)",
     "Giọng trợ lý",
     "Ngoài phạm vi ASR; thuộc đánh giá TTS sản phẩm",
     "Giữ cho giai đoạn sau. Không đưa vào dữ liệu huấn luyện ASR."),
]

# ------------------------------------------------------------------ case study theo mục đích
# (id, tên, mô tả, mục đích chính, liên quan ASR, phần người dùng (M1/M2), phần trợ lý (M5), lý do, yếu tố trọng yếu, preset, ghi chú)
CASES = [
    ("CS01", "Dẫn đường", "Chỉ đường từng chặng: rẽ, khoảng cách, tên đường, đích đến.", "M1", "Có",
     "dẫn đường đến địa chỉ; hỏi còn bao xa; tìm đường tránh tắc; hỏi giờ đến; hủy dẫn đường",
     "báo rẽ, báo khoảng cách, báo đã đến, đổi lộ trình",
     "Người dùng nói địa chỉ, số nhà, tên đường nhiều nhất; tên riêng và từ địa phương (hẻm/ngõ, quẹo/rẽ) là lỗi hay gặp.",
     "E03; E04; S51; S53; S54; D01", "E02; E03; E12; E10; E13", ""),
    ("CS02", "Cảnh báo an toàn (ADAS)", "Cảnh báo va chạm, lệch làn, mệt mỏi, điểm mù, quá tốc độ.", "M5", "Hầu như không",
     "tắt hoặc bật cảnh báo; nói 'tôi ổn' khi bị nhắc mệt",
     "va chạm phía trước, lệch làn, người lái mệt, điểm mù, vượt tốc độ",
     "Gần như toàn bộ do hệ thống tự phát. Phần người dùng rất nhỏ nên chỉ lấy một lát để thử giọng mệt mỏi.",
     "D03; S21; S22; S23", "E03; E05; E07; E04; E14", "Trọng số sinh thấp."),
    ("CS03", "Điều khiển xe", "Điều chỉnh điều hòa, ghế, cửa kính, cửa sổ trời, đèn trong xe bằng giọng nói.", "M1", "Có",
     "đặt nhiệt độ; sưởi ghế; hạ kính; chỉnh quạt; bật sấy kính",
     "xác nhận thông số",
     "Lệnh ngắn, nhiều thông số; có từ vùng (kính/kiếng, điều hòa/máy lạnh) và chuyển mã (air-con).",
     "E02; E03; S51; S52; S55; A04", "E01; E02; E06; E05", "Lõi của bộ M1."),
    ("CS04", "Giải trí (nhạc, radio)", "Phát nhạc, chuyển kênh radio, chỉnh âm lượng.", "M1", "Có",
     "mở bài hoặc danh sách nhạc; chuyển kênh; chỉnh âm lượng; hỏi đang phát gì",
     "xác nhận bài, kênh",
     "Tên bài, tên kênh, từ mượn tiếng Anh; nhạc đang phát là nguồn ồn chính.",
     "E05; E07; S55; A07; A14", "E07; E02; E08; E17", ""),
    ("CS05", "Điện thoại và tin nhắn", "Báo cuộc gọi, đọc tin nhắn, gọi theo số hoặc tên.", "M1", "Có",
     "gọi tên; gọi số; đọc tin nhắn; trả lời tin nhắn",
     "báo cuộc gọi đến, đọc tin nhắn",
     "Số điện thoại, tên người, xưng hô theo vùng (mạ/má/mẹ); hành khách nói chen.",
     "E03; E06; S52; S53; A14", "E11; E02; E07; E15", ""),
    ("CS06", "Trạng thái xe và bảo dưỡng", "Báo áp suất lốp, nhiên liệu, bảo dưỡng định kỳ, đèn báo.", "M1", "Một phần",
     "hỏi áp suất lốp; hỏi nhiên liệu còn lại; hỏi lịch bảo dưỡng",
     "cảnh báo áp suất, nhiên liệu, đèn báo",
     "Phần lớn là hệ thống báo; người dùng chỉ hỏi lại, câu hỏi ngắn.",
     "E03; E07; D01", "E01; E02; E03", ""),
    ("CS07", "Sạc xe điện và trạm nhiên liệu", "Hỏi tình trạng pin, tìm trạm sạc, ước tính thời gian và chi phí sạc.", "M1", "Có",
     "hỏi pin còn lại; tìm trạm sạc; hỏi thời gian và chi phí sạc",
     "báo pin, trạm gần nhất, chi phí",
     "Số thập phân, phần trăm, tiền VND; cách đọc nghìn/ngàn theo vùng.",
     "E03; E07; S53", "E01; E08; E02", ""),
    ("CS08", "Giao thông và thời tiết", "Báo tắc đường, tai nạn, giờ đến dự kiến, dự báo thời tiết.", "M1", "Có",
     "hỏi tắc đường phía trước; hỏi thời tiết; hỏi giờ đến",
     "bản tin giao thông, thời tiết",
     "Tên địa danh, giờ, khoảng giá trị; từ vùng (kẹt xe/tắc đường).",
     "E03; E04; S51; D01", "E12; E04; E02", ""),
    ("CS09", "Khẩn cấp và cứu hộ", "Phát hiện va chạm nghiêm trọng, sự cố pin, gọi cấp cứu và cứu hộ.", "M1", "Một phần",
     "gọi cấp cứu; nói 'tôi ổn'; kêu cứu; gọi cứu hộ",
     "hỏi thăm, gửi vị trí, hướng dẫn rời xe",
     "Người dùng nói trong căng thẳng, to, nhanh, cao giọng (Lombard, cảm xúc). Khó sinh và chưa có bằng chứng; số mẫu ít.",
     "D03; S21; S22; S23; S24; E08", "E03; E01; E04; E17", "Khó nhất về mặt giọng."),
    ("CS10", "Hội thoại và gợi ý chủ động", "Gợi ý lịch trình, quán gần đây, nhắc việc, hỏi đáp tự nhiên.", "M1", "Có",
     "nhắc việc; hỏi quán gần đây; cảm ơn; hỏi đáp chung",
     "gợi ý, nhắc lịch",
     "Câu dài hơn, câu cụt, chuyển mã Anh–Việt; đa dạng diễn đạt lớn nhất.",
     "E05; E06; E08; S23; S33; S55", "E01; E02; E08", ""),
    ("CS11", "Hành khách và trẻ em", "Thông báo cho khoang sau, nhắc dây an toàn ghế sau, nói chuyện với trẻ.", "M1", "Một phần",
     "trẻ nhờ mở nhạc; người lớn ra lệnh cho khoang sau; tắt loa sau",
     "nhắc dây an toàn, chế độ yên tĩnh khoang sau",
     "Cần giọng trẻ em, vốn không tạo được từ giọng người lớn một cách đáng tin; cần nguồn giọng trẻ thật có đồng ý.",
     "S12; A14; E06; S21", "E02; E07; E08", "Chỉ làm khi có nguồn giọng trẻ em."),
    ("CS12", "Lỗi, làm rõ và ngoại tuyến", "Xử lý khi không nghe rõ, trùng tên, mất mạng, tính năng chưa hỗ trợ.", "M2", "Có",
     "nói lại; sửa 'không phải, ý tôi là…'; chọn cái thứ hai; hủy",
     "xin lỗi, hỏi lại, báo mất mạng",
     "Phần lớn là câu trả lời rất ngắn, đúng chỗ TTS dễ lỗi và ASR dễ nhầm.",
     "E08; S23; S33; E06", "E02; E03; E07; E10; E16", "Gần hết là M2."),
]
CASE_NAME = {c[0]: c[1] for c in CASES}

# ma trận: case -> {mã yếu tố: "●" (trọng yếu) | "○" (xuất hiện)}
MATRIX_COLS = ["E02", "E03", "E04", "E05", "E06", "E07", "E08", "D01", "D03", "S21", "S22", "S23", "S24",
               "S33", "S51", "S52", "S53", "S54", "S55", "S12", "A07", "A14"]
MATRIX = {
    "CS01": {"E03": "●", "E04": "●", "E05": "○", "E07": "○", "E08": "○", "D01": "●", "S23": "○", "S33": "○", "S51": "●", "S53": "○", "S54": "●"},
    "CS02": {"E08": "●", "D01": "●", "D03": "●", "S21": "●", "S22": "○", "S23": "●"},
    "CS03": {"E02": "●", "E03": "●", "E05": "○", "E06": "○", "E08": "○", "S51": "●", "S52": "○", "S55": "●", "A14": "○"},
    "CS04": {"E03": "○", "E05": "●", "E07": "○", "S33": "○", "S55": "●", "A07": "●", "A14": "○"},
    "CS05": {"E03": "●", "E04": "○", "E06": "●", "S52": "●", "S53": "●", "A14": "●"},
    "CS06": {"E03": "●", "E07": "●", "E08": "○", "D01": "○"},
    "CS07": {"E03": "●", "E07": "●", "E08": "○", "S53": "●"},
    "CS08": {"E03": "●", "E04": "●", "E08": "○", "D01": "○", "S51": "○"},
    "CS09": {"E08": "●", "D01": "●", "D03": "●", "S21": "●", "S22": "○", "S23": "●", "S24": "●"},
    "CS10": {"E03": "○", "E05": "●", "E06": "○", "E08": "●", "S23": "○", "S33": "●", "S55": "●"},
    "CS11": {"E06": "○", "S12": "●", "S21": "○", "A14": "●"},
    "CS12": {"E06": "●", "E08": "●", "S23": "●", "S33": "●", "S51": "○"},
}

# ------------------------------------------------------------------ câu mẫu của người dùng
# vocab trạng thái người nói
STATES = ["Bình thường", "Vội / nói nhanh", "Căng thẳng / khẩn", "Mệt mỏi", "Nói trong ồn (Lombard)", "Trẻ em"]
ACTS = ["Lệnh", "Câu hỏi", "Trả lời ngắn", "Câu cụt", "Kêu cứu"]
LEXV = ["Chuẩn chung", "Bắc", "Trung", "Nam"]
REGV = ["Bắc", "Trung", "Nam", "Bất kỳ (xoay vòng)"]

M_ROWS = []


def add(purpose, case, intent, act, raw, spoken, lang="Việt", feats="", lex="Chuẩn chung", region=None, state="Bình thường",
        factors="", notes=""):
    if region is None:
        region = {"Bắc": "Bắc", "Trung": "Trung", "Nam": "Nam"}.get(lex, "Bất kỳ (xoay vòng)")
    M_ROWS.append(dict(purpose=purpose, case=case, intent=intent, act=act, raw=raw, spoken=spoken, lang=lang, feats=feats,
                       lex=lex, region=region, state=state, factors=factors, notes=notes))


V = "Cần người bản ngữ vùng đó duyệt."
# CS01
add("M1", "CS01", "dẫn đường đến địa chỉ", "Lệnh", "Dẫn đường đến số 15 ngõ 28 Chùa Bộc.", "Dẫn đường đến số mười lăm ngõ hai mươi tám Chùa Bộc.",
    feats="số; địa chỉ; tên riêng/địa danh", lex="Bắc", factors="E03; E04; S51; S54", notes=V)
add("M1", "CS01", "dẫn đường đến địa chỉ", "Lệnh", "Dẫn đường tới hẻm 28 đường Nguyễn Văn Cừ.", "Dẫn đường tới hẻm hai mươi tám đường Nguyễn Văn Cừ.",
    feats="số; địa chỉ; tên riêng/địa danh", lex="Nam", factors="E03; E04; S51; S54", notes=V)
add("M1", "CS01", "hỏi còn bao xa", "Câu hỏi", "Còn bao xa nữa thì đến nơi?", "Còn bao xa nữa thì đến nơi?", factors="E08; S33")
add("M1", "CS01", "báo rẽ ở ngã tư", "Câu hỏi", "Quẹo trái ở ngã tư tới đúng không?", "Quẹo trái ở ngã tư tới đúng không?",
    lex="Nam", factors="S51; S33", notes=V)
add("M1", "CS01", "tìm đường tránh tắc", "Lệnh", "Tìm đường khác tránh kẹt xe.", "Tìm đường khác tránh kẹt xe.", lex="Nam", factors="S51", notes=V)
add("M1", "CS01", "tìm đường tránh tắc", "Lệnh", "Tìm đường khác tránh tắc đường.", "Tìm đường khác tránh tắc đường.", lex="Bắc", factors="S51", notes=V)
add("M1", "CS01", "hỏi giờ đến", "Câu hỏi", "Đến Huế mất bao lâu?", "Đến Huế mất bao lâu?", feats="tên riêng/địa danh", region="Trung",
    factors="E04; E08", notes="Giọng Trung nói tên địa danh Trung; từ vựng chuẩn chung.")
add("M1", "CS01", "hủy dẫn đường", "Lệnh", "Hủy dẫn đường.", "Hủy dẫn đường.", factors="E08")
# CS02
add("M1", "CS02", "tắt cảnh báo", "Lệnh", "Tắt cảnh báo lệch làn.", "Tắt cảnh báo lệch làn.", factors="E08")
add("M1", "CS02", "nói tôi ổn khi bị nhắc mệt", "Câu cụt", "Tôi tỉnh rồi, không cần nhắc nữa.", "Tôi tỉnh rồi, không cần nhắc nữa.",
    state="Mệt mỏi", factors="S22; S23; D03", notes="Giọng mệt khó sinh; xem yếu tố S22.")
# CS03
add("M1", "CS03", "đặt nhiệt độ ghế", "Lệnh", "Đặt nhiệt độ ghế lái 24 độ.", "Đặt nhiệt độ ghế lái hai mươi tư độ.", feats="số; đơn vị đo", factors="E03; E02")
add("M1", "CS03", "hạ kính", "Lệnh", "Hạ kính bên phụ xuống một nửa.", "Hạ kính bên phụ xuống một nửa.", lex="Bắc", factors="S51; E02", notes=V)
add("M1", "CS03", "hạ kính", "Lệnh", "Hạ kiếng bên phụ xuống một nửa nha.", "Hạ kiếng bên phụ xuống một nửa nha.", lex="Nam", factors="S51; S52; E02", notes=V)
add("M1", "CS03", "bật sưởi ghế", "Lệnh", "Bật sưởi ghế mức 2.", "Bật sưởi ghế mức hai.", feats="số", factors="E03; E02")
add("M1", "CS03", "bật điều hòa", "Lệnh", "Bật điều hòa 19 độ.", "Bật điều hòa mười chín độ.", feats="số; đơn vị đo", lex="Bắc", factors="E03; S51", notes=V)
add("M1", "CS03", "bật điều hòa", "Lệnh", "Bật máy lạnh 19 độ.", "Bật máy lạnh mười chín độ.", feats="số; đơn vị đo", lex="Nam", factors="E03; S51", notes=V)
add("M1", "CS03", "bật điều hòa", "Câu cụt", "Bật air-con lên chút.", "Bật air-con lên chút.", lang="Việt + Anh", feats="từ mượn tiếng Anh", factors="S55; S23",
    notes="Cách đọc 'air-con' cần thống nhất.")
add("M1", "CS03", "chỉnh quạt", "Lệnh", "Tăng quạt gió lên mức 3.", "Tăng quạt gió lên mức ba.", feats="số", factors="E03; E02")
add("M1", "CS03", "mở cửa sổ trời", "Lệnh", "Mở cửa sổ trời.", "Mở cửa sổ trời.", factors="E08")
# CS04
add("M1", "CS04", "mở danh sách nhạc", "Lệnh", "Mở danh sách nhạc Chill cuối tuần.", "Mở danh sách nhạc Chill cuối tuần.", lang="Việt + Anh",
    feats="từ mượn tiếng Anh; tên riêng/địa danh", factors="E05; A07")
add("M1", "CS04", "chuyển kênh radio", "Lệnh", "Chuyển sang kênh VOV Giao thông, FM 91 MHz.", "Chuyển sang kênh V O V Giao thông, F M chín mươi mốt mê ga héc.",
    lang="Việt + Anh", feats="viết tắt; tần số/công suất; số", factors="E03; E07; E05")
add("M1", "CS04", "chỉnh âm lượng", "Lệnh", "Tăng âm lượng lên 18.", "Tăng âm lượng lên mười tám.", feats="số", state="Nói trong ồn (Lombard)", factors="E03; S24; A07")
add("M1", "CS04", "hỏi đang phát gì", "Câu hỏi", "Bài này ai hát vậy?", "Bài này ai hát vậy?", lex="Nam", factors="S51; S33", notes=V)
add("M1", "CS04", "chuyển bài", "Lệnh", "Bật bài tiếp theo.", "Bật bài tiếp theo.", factors="E08")
# CS05
add("M1", "CS05", "gọi tên", "Lệnh", "Gọi cho anh Minh.", "Gọi cho anh Minh.", feats="tên riêng/địa danh", factors="E06; E04")
add("M1", "CS05", "gọi mẹ", "Lệnh", "Gọi cho mạ.", "Gọi cho mạ.", lex="Trung", factors="S52; S51", notes="Chỉ ví dụ; " + V)
add("M1", "CS05", "gọi mẹ", "Lệnh", "Gọi cho má.", "Gọi cho má.", lex="Nam", factors="S52; S51", notes=V)
add("M1", "CS05", "gọi theo số", "Lệnh", "Gọi số 0912 345 678.", "Gọi số không chín một hai, ba bốn năm, sáu bảy tám.", feats="số điện thoại; số",
    state="Vội / nói nhanh", factors="E03; S53; S34")
add("M1", "CS05", "đọc tin nhắn", "Lệnh", "Đọc tin nhắn mới.", "Đọc tin nhắn mới.", factors="E08; A14")
add("M1", "CS05", "trả lời tin nhắn", "Lệnh", "Trả lời tin nhắn là mình đến muộn 10 phút.", "Trả lời tin nhắn là mình đến muộn mười phút.", feats="số",
    factors="E03; E06")
# CS06
add("M1", "CS06", "hỏi áp suất lốp", "Câu hỏi", "Áp suất lốp trước bên phải bao nhiêu?", "Áp suất lốp trước bên phải bao nhiêu?", factors="E07; E03")
add("M1", "CS06", "hỏi nhiên liệu", "Câu hỏi", "Còn bao nhiêu xăng?", "Còn bao nhiêu xăng?", factors="E08")
add("M1", "CS06", "hỏi bảo dưỡng", "Câu hỏi", "Bao giờ phải bảo dưỡng?", "Bao giờ phải bảo dưỡng?", lex="Bắc", factors="S51", notes=V)
# CS07
add("M1", "CS07", "tìm trạm sạc", "Câu hỏi", "Trạm sạc gần nhất ở đâu?", "Trạm sạc gần nhất ở đâu?", factors="E08")
add("M1", "CS07", "thời gian sạc", "Câu hỏi", "Sạc từ 20% lên 80% mất bao lâu?", "Sạc từ hai mươi phần trăm lên tám mươi phần trăm mất bao lâu?",
    feats="phần trăm; số", factors="E03; E07")
add("M1", "CS07", "chi phí sạc", "Câu hỏi", "Sạc đầy hết bao nhiêu tiền?", "Sạc đầy hết bao nhiêu tiền?", factors="S53")
add("M1", "CS07", "hỏi pin", "Câu hỏi", "Pin còn bao nhiêu phần trăm?", "Pin còn bao nhiêu phần trăm?", feats="phần trăm", factors="E07")
# CS08
add("M1", "CS08", "hỏi thời tiết", "Câu hỏi", "Hôm nay Đà Nẵng có mưa không?", "Hôm nay Đà Nẵng có mưa không?", feats="tên riêng/địa danh", region="Trung", factors="E04")
add("M1", "CS08", "hỏi tắc đường", "Câu hỏi", "Phía trước có kẹt xe không?", "Phía trước có kẹt xe không?", lex="Nam", factors="S51", notes=V)
add("M1", "CS08", "hỏi tắc đường", "Câu hỏi", "Phía trước có tắc đường không?", "Phía trước có tắc đường không?", lex="Bắc", factors="S51", notes=V)
add("M1", "CS08", "hỏi giờ đến", "Câu hỏi", "Mấy giờ thì tới nơi?", "Mấy giờ thì tới nơi?", factors="D01")
# CS09
add("M1", "CS09", "gọi cấp cứu", "Lệnh", "Gọi cấp cứu 115.", "Gọi cấp cứu một một năm.", feats="số", state="Căng thẳng / khẩn", factors="D03; S21; S23; S24",
    notes="Số khẩn cấp đọc từng chữ số.")
add("M1", "CS09", "nói tôi ổn", "Câu cụt", "Tôi ổn, không cần gọi.", "Tôi ổn, không cần gọi.", state="Căng thẳng / khẩn", factors="D03; S23")
add("M1", "CS09", "kêu cứu", "Kêu cứu", "Giúp tôi với!", "Giúp tôi với!", state="Căng thẳng / khẩn", factors="D03; S21; S24")
add("M1", "CS09", "gọi cứu hộ", "Lệnh", "Gọi cứu hộ giao thông.", "Gọi cứu hộ giao thông.", state="Căng thẳng / khẩn", factors="D03; E08")
# CS10
add("M1", "CS10", "nhắc việc", "Lệnh", "Nhắc tôi mua sữa khi đi ngang siêu thị.", "Nhắc tôi mua sữa khi đi ngang siêu thị.", factors="E08; E06")
add("M1", "CS10", "nhắc lịch", "Lệnh", "Nhắc tôi họp lúc 9 giờ sáng mai.", "Nhắc tôi họp lúc chín giờ sáng mai.", feats="giờ/ngày/tháng/năm; số", factors="E03")
add("M1", "CS10", "hỏi quán gần đây", "Câu hỏi", "Gần đây có quán cà phê nào có chỗ đậu xe không?", "Gần đây có quán cà phê nào có chỗ đậu xe không?",
    lex="Nam", factors="S51; E08", notes=V)
add("M1", "CS10", "hỏi quán gần đây", "Câu hỏi", "Gần đây có quán cà phê nào có chỗ đỗ xe không?", "Gần đây có quán cà phê nào có chỗ đỗ xe không?",
    lex="Bắc", factors="S51; E08", notes=V)
add("M1", "CS10", "cảm ơn", "Câu cụt", "Ok, cảm ơn.", "Ô kê, cảm ơn.", lang="Việt + Anh", feats="từ mượn tiếng Anh", factors="S55; S23; E08")
# CS11
add("M1", "CS11", "trẻ nhờ mở nhạc", "Lệnh", "Con muốn nghe nhạc.", "Con muốn nghe nhạc.", state="Trẻ em", factors="S12; A14",
    notes="Cần nguồn giọng trẻ em thật có đồng ý; không tạo từ giọng người lớn.")
add("M1", "CS11", "mở nhạc cho bé", "Lệnh", "Bật nhạc thiếu nhi cho bé nghe.", "Bật nhạc thiếu nhi cho bé nghe.", factors="E06; A14")
add("M1", "CS11", "tắt loa sau", "Lệnh", "Tắt loa phía sau.", "Tắt loa phía sau.", factors="E08")
# CS12 và M2
add("M2", "CS12", "nói lại", "Trả lời ngắn", "Nói lại đi.", "Nói lại đi.", factors="E08; S33")
add("M2", "CS12", "sửa lệnh", "Câu cụt", "Không phải, ý tôi là gọi anh Hùng Trần.", "Không phải, ý tôi là gọi anh Hùng Trần.", feats="tên riêng/địa danh",
    factors="S23; E06; S34")
add("M2", "CS12", "chọn", "Trả lời ngắn", "Cái thứ hai.", "Cái thứ hai.", factors="E08; S33")
add("M2", "CS12", "chọn", "Trả lời ngắn", "Cái thứ nhất.", "Cái thứ nhất.", factors="E08")
add("M2", "CS12", "xác nhận", "Trả lời ngắn", "Có.", "Có.", factors="E08; S33")
add("M2", "CS12", "từ chối", "Trả lời ngắn", "Không.", "Không.", factors="E08; S33")
add("M2", "CS12", "xác nhận", "Trả lời ngắn", "Đúng rồi.", "Đúng rồi.", factors="E08")
add("M2", "CS12", "xác nhận lịch sự", "Trả lời ngắn", "Vâng, đồng ý.", "Vâng, đồng ý.", lex="Bắc", factors="S52; E08", notes=V)
add("M2", "CS12", "xác nhận lịch sự", "Trả lời ngắn", "Dạ, có.", "Dạ, có.", lex="Nam", factors="S52; E08", notes=V)
add("M2", "CS12", "hủy", "Trả lời ngắn", "Hủy.", "Hủy.", factors="E08")
add("M2", "CS12", "chọn số", "Trả lời ngắn", "Hai.", "Hai.", feats="số", factors="E03; E08")
add("M2", "CS12", "trả lời giờ", "Trả lời ngắn", "Chín giờ.", "Chín giờ.", feats="giờ/ngày/tháng/năm", factors="E03; E08")
# M4: câu chẩn đoán
add("M4", "CS03", "rất ngắn", "Lệnh", "Mở cửa.", "Mở cửa.", factors="E08", notes="Thử câu 2 âm tiết.")
add("M4", "CS01", "rất ngắn", "Lệnh", "Rẽ phải.", "Rẽ phải.", lex="Bắc", factors="E08; S51")
add("M4", "CS12", "rất ngắn", "Trả lời ngắn", "Dừng.", "Dừng.", factors="E08", notes="Thử câu 1 âm tiết.")
add("M4", "CS05", "dãy số", "Lệnh", "Gọi số 0903 456 789.", "Gọi số không chín không ba, bốn năm sáu, bảy tám chín.", feats="số điện thoại; số", factors="E03")
add("M4", "CS10", "thanh hỏi và ngã", "Câu hỏi", "Anh ấy nghỉ rồi.", "Anh ấy nghỉ rồi.", factors="E02; S43", notes="Cặp tối thiểu với dòng kế tiếp (nghỉ / nghĩ).")
add("M4", "CS10", "thanh hỏi và ngã", "Câu hỏi", "Anh ấy nghĩ rồi.", "Anh ấy nghĩ rồi.", factors="E02; S43", notes="Cặp tối thiểu với dòng trước.")
add("M4", "CS08", "thanh hỏi và ngã", "Câu hỏi", "Bão sắp tới, tôi đã bảo anh rồi.", "Bão sắp tới, tôi đã bảo anh rồi.", factors="E02; S43",
    notes="Có cả bão (ngã) và bảo (hỏi) trong một câu.")
add("M4", "CS07", "cách đọc số theo vùng", "Câu hỏi", "Số 105 có đúng không?", "Số một trăm linh năm có đúng không?", feats="số", lex="Bắc", factors="S53; E03", notes=V)
add("M4", "CS07", "cách đọc số theo vùng", "Câu hỏi", "Số 105 có đúng không?", "Số một trăm lẻ năm có đúng không?", feats="số", lex="Nam", factors="S53; E03", notes=V)
add("M4", "CS07", "cách đọc tiền theo vùng", "Câu hỏi", "Giá 1.200 đồng đúng không?", "Giá một nghìn hai trăm đồng đúng không?", feats="tiền VND; số", lex="Bắc", factors="S53; E03", notes=V)
add("M4", "CS07", "cách đọc tiền theo vùng", "Câu hỏi", "Giá 1.200 đồng đúng không?", "Giá một ngàn hai trăm đồng đúng không?", feats="tiền VND; số", lex="Nam", factors="S53; E03", notes=V)
add("M4", "CS01", "tên đường dài", "Lệnh", "Dẫn đường đến phố Nguyễn Thị Minh Khai.", "Dẫn đường đến phố Nguyễn Thị Minh Khai.", feats="tên riêng/địa danh", factors="E04; S44")
add("M4", "CS08", "từ vùng miền Trung", "Câu hỏi", "Phía trước kẹt xe, rứa có đi đường khác không?", "Phía trước kẹt xe, rứa có đi đường khác không?", lex="Trung", factors="S51; S43",
    notes="Chỉ ví dụ 'rứa'; cần người bản ngữ Trung Bộ bổ sung thêm từ.")
add("M4", "CS03", "chuyển mã", "Lệnh", "Bật air-con lên mười chín độ.", "Bật air-con lên mười chín độ.", lang="Việt + Anh", feats="từ mượn tiếng Anh; số", factors="S55; E05")

# ------------------------------------------------------------------ khung câu (mẫu × khe)
# (id, case, intent, mẫu, slot1 tên, slot1 ví dụ, slot1 số giá trị mục tiêu, slot2..., slot3..., biến thể vùng, yếu tố, ghi chú)
TEMPLATES = [
    ("T01", "CS01", "dẫn đường đến địa chỉ", "{động từ} đến {đích}",
     ("động từ", "Dẫn đường; Chỉ đường tới; Đưa tôi đến", 4), ("đích", "số 15 ngõ 28 Chùa Bộc; hẻm 28 đường Nguyễn Văn Cừ; sân bay Nội Bài; bệnh viện Chợ Rẫy; Huế", 300), None,
     "ngõ/hẻm theo vùng của địa chỉ", "E03; E04; S51; S54", "Danh sách đích lấy từ dữ liệu bản đồ (OpenStreetMap, ODbL, cần ghi nguồn) kèm cách gọi quen của người địa phương."),
    ("T02", "CS01", "hỏi khoảng cách hoặc thời gian", "{hỏi} đến {đích}", ("hỏi", "Còn bao xa; Mất bao lâu; Mấy giờ thì tới", 5), ("đích", "Huế; Đà Nẵng; nhà; cơ quan", 300), None,
     "", "E04; E08; S33", ""),
    ("T03", "CS01", "tìm đường tránh", "Tìm đường khác tránh {trở ngại}", ("trở ngại", "kẹt xe (Nam); tắc đường (Bắc); công trình; ngập nước", 8), None, None,
     "kẹt xe/tắc đường", "S51", ""),
    ("T04", "CS03", "đặt nhiệt độ", "Đặt nhiệt độ {vị trí} {số} độ", ("vị trí", "ghế lái; ghế phụ; khoang sau", 3), ("số", "18; 22; 24; 28", 11), None,
     "", "E03; E02", ""),
    ("T05", "CS03", "hạ kính", "Hạ {kính} {bên} xuống {mức}", ("kính", "kính (Bắc); kiếng (Nam)", 2), ("bên", "bên lái; bên phụ; sau trái; sau phải", 4), ("mức", "một nửa; hoàn toàn; một chút", 3),
     "kính/kiếng; thêm nha/nhé", "S51; S52; E02", ""),
    ("T06", "CS03", "bật điều hòa", "Bật {điều hòa} {số} độ", ("điều hòa", "điều hòa (Bắc); máy lạnh (Nam); air-con", 3), ("số", "16; 19; 22; 26", 11), None,
     "điều hòa/máy lạnh", "E03; S51; S55", ""),
    ("T07", "CS04", "mở nhạc", "Mở {loại} {tên}", ("loại", "bài; danh sách nhạc; podcast", 3), ("tên", "Chill cuối tuần; nhạc thiếu nhi", 100), None,
     "", "E05; A07", "Tên lấy từ kho nhạc; kiểm bản quyền nếu đưa lời bài hát."),
    ("T08", "CS04", "chuyển kênh", "Chuyển sang kênh {kênh}, {tần số}", ("kênh", "VOV Giao thông; VOV 3", 10), ("tần số", "FM 91 MHz; FM 102,7 MHz", 10), None,
     "", "E03; E07; E05", ""),
    ("T09", "CS05", "gọi", "Gọi cho {người}", ("người", "anh Minh; chị Lan; mạ (Trung); má (Nam)", 100), None, None,
     "xưng hô mạ/má/mẹ", "E06; S52", "Tên người dùng tên phổ biến, không dùng tên người có thật."),
    ("T10", "CS05", "gọi theo số", "Gọi số {số điện thoại}", ("số điện thoại", "0912 345 678; 0903 456 789", 200), None, None,
     "", "E03; S53", ""),
    ("T11", "CS06", "hỏi trạng thái xe", "{vật} {bộ phận} {hỏi}", ("vật", "Áp suất lốp; Nhiên liệu; Lịch bảo dưỡng", 4), ("bộ phận", "trước bên phải; sau bên trái", 4), ("hỏi", "bao nhiêu; còn bao nhiêu", 3),
     "bao giờ/khi nào", "E03; E07", ""),
    ("T12", "CS07", "hỏi sạc", "Sạc từ {x} lên {y} phần trăm mất bao lâu", ("x", "20; 35; 50", 8), ("y", "80; 90; 100", 4), None,
     "", "E03; E07", ""),
    ("T13", "CS08", "hỏi thời tiết", "Hôm nay {thành phố} có {hiện tượng} không", ("thành phố", "Hà Nội; Đà Nẵng; Huế; Cần Thơ", 63), ("hiện tượng", "mưa; nắng; ngập", 4), None,
     "", "E04", ""),
    ("T14", "CS09", "gọi khẩn cấp", "Gọi {dịch vụ}", ("dịch vụ", "cấp cứu 115; cứu hộ giao thông", 4), None, None,
     "", "D03; S23", "Trạng thái giọng căng thẳng; ít mẫu."),
    ("T15", "CS10", "nhắc việc", "Nhắc tôi {việc} {lúc}", ("việc", "mua sữa; họp; đón con", 100), ("lúc", "lúc chín giờ sáng mai; khi đi ngang siêu thị", 20), None,
     "", "E03; E08", ""),
    ("T16", "CS10", "hỏi quán gần đây", "Gần đây có {quán} nào có chỗ {đỗ} xe không", ("quán", "quán cà phê; nhà hàng; trạm sạc", 10), ("đỗ", "đỗ (Bắc); đậu (Nam)", 2), None,
     "đỗ/đậu", "S51; E08", ""),
    ("T17", "CS12", "trả lời ngắn", "{trả lời}", ("trả lời", "Có; Không; Hủy; Cái thứ hai; Hai", 40), None, None,
     "vâng/dạ", "E08; S33; S52", "Câu rất ngắn."),
    ("T18", "CS12", "sửa lệnh", "Không phải, ý tôi là {lệnh đúng}", ("lệnh đúng", "gọi anh Hùng Trần; đi đường khác", 100), None, None,
     "", "S23; E06", ""),
]

# ------------------------------------------------------------------ nguồn ồn thật cho preset
PRESET_REAL = {
    "E01": ("Có", "Nền yên tĩnh hoặc không trộn; làm đối chứng."),
    "E02": ("Có", "AISHELL-5 (nền ồn trong xe khoảng 40 giờ, chưa rõ điều kiện chạy) hoặc CAVEMOVE (ồn khi xe chạy); cần nghe và phân loại trước."),
    "E03": ("Có", "Như E02; cần chọn đoạn tốc độ cao nếu có nhãn."),
    "E04": ("Có", "Chưa tìm được nguồn mưa trong xe; tự ghi hoặc kho âm thanh công khai (chưa kiểm giấy phép)."),
    "E05": ("Có", "Chưa tìm được nguồn; tự ghi một xe nếu có."),
    "E06": ("Có", "Tự ghi quạt điều hòa hoặc kho công khai (chưa kiểm giấy phép)."),
    "E07": ("Có", "Trộn nhạc (kiểm bản quyền) và giọng người từ kho giọng thật làm nền nhiều người nói."),
    "E08": ("Có", "Chưa tìm được nguồn xe điện; tự ghi nếu có."),
    "E09": ("Có", "Chưa tìm được nguồn; tự ghi nếu có."),
    "E10": ("Có", "Cần đáp ứng xung hầm; chưa tìm được nguồn, có thể mô phỏng."),
    "E11": ("Một phần", "Codec Bluetooth tất định (SBC, mSBC); chỉ áp dụng nếu mic đi qua Bluetooth."),
    "E12": ("Có", "Còi xe từ kho âm thanh công khai (chưa kiểm giấy phép) trộn lên nền nội đô."),
    "E13": ("Có", "Ghép hai nền ồn theo thời gian (nội đô sang hầm)."),
    "E14": ("Có", "Âm báo của xe: thu từ một xe thật hoặc từ tài liệu hãng."),
    "E15": ("Một phần", "Codec cuộc gọi tất định; chỉ áp dụng khi tiếng nói đi qua điện thoại."),
    "E16": ("Không", "Dành cho TTS chạy đám mây phát ra loa; thuộc M5, ngoài phạm vi ASR."),
    "E17": ("Không", "Dành cho loa quá tải khi phát; thuộc M5, ngoài phạm vi ASR."),
}

# ------------------------------------------------------------------ đánh giá giải pháp
# (mã, khoảng trống, giải pháp, bằng chứng, hiệu quả, khả thi, an toàn, căn cứ)
SOLUTIONS_EVAL = [
    ("S1", "Giữ giọng vùng", "Tinh chỉnh TTS trên giọng có nhãn vùng, cân bằng ba miền", 7, 8, 6, 5,
     "Singlish: độ giống giọng vùng của Chatterbox 0,51 → 0,64, có cả trên người nói chưa thấy; nhưng WER 11,5% → 15,4%. Chỉ thử trên tiếng Anh."),
    ("S2", "Giữ giọng vùng", "Chọn đoạn giọng tham chiếu cùng vùng (kiểu CLARITY)", 5, 5, 9, 8,
     "CLARITY (chỉ đọc tóm tắt): viết lại text cho đúng phương ngữ và dùng đoạn tham chiếu cùng giọng; zero-shot vốn yếu ở giọng vùng."),
    ("S3", "Giữ giọng vùng", "Điều kiện theo mã người nói (tập giọng đóng)", 6, 7, 5, 6,
     "Singlish: bản điều kiện theo mã người nói giữ giọng vùng tốt nhất (0,66) nhưng chỉ chạy với người đã thấy; cần nhiều giờ mỗi người."),
    ("S4", "Giữ giọng vùng", "Điều hướng giọng không cần huấn luyện (activation steering, accent vector)", 4, 4, 3, 4,
     "Chỉ đọc tóm tắt; chủ yếu để bỏ hoặc điều khiển giọng trong tiếng Anh, trong khi bạn cần thêm giọng Trung."),
    ("S5", "Độ giống người nói", "Chọn và làm sạch đoạn tham chiếu, đo bằng độ giống người nói", 5, 6, 9, 8,
     "WildSpoof (tóm tắt): làm sạch đoạn tham chiếu tăng độ bền; chưa đọc kết quả về độ dài và chất lượng đoạn."),
    ("S6", "Độ giống người nói", "Coi độ giống là ràng buộc; ưu tiên số người nói và đa dạng câu", 7, 8, 9, 7,
     "Ogun et al. và Versatile TTS: thêm người nói chỉ giảm WER khoảng 2%; khoảng 50–100 người nói là đủ (Mân Nam, tiếng Anh)."),
    ("S7", "Từ địa phương", "Viết lại text theo từ vựng vùng, người bản ngữ duyệt", 5, 5, 9, 8,
     "Cần nhưng không đủ một mình: từ vựng đổi được bằng text, cách phát âm thì không (Jewell 2022)."),
    ("S8", "Số câu quá ít", "Mở rộng lên hàng nghìn câu khác nhau (mẫu × khe, LLM diễn đạt lại, người duyệt)", 8, 9, 8, 6,
     "Versatile TTS: đa dạng câu quan trọng hơn đa dạng người nói; dưới khoảng 10.000 câu thì CER tăng rõ (Mân Nam)."),
    ("S9", "Nhiễu xe", "Trộn nhiễu và vang vào âm thanh TTS khi tạo dữ liệu ASR", 8, 7, 10, 9,
     "Ogun et al.: nhiễu giảm WER 5,1%, nhiễu cộng vang 6,6% (tiếng Anh)."),
    ("S10", "Lombard", "Điều khiển TTS theo kiểu Lombard", 3, 4, 3, 4,
     "Paper Lombard TTS (tóm tắt): chưa có số liệu ASR."),
    ("S12", "Lỗi đầu ra", "Lọc bằng ASR hai chiều và tỷ lệ độ dài, kiểm tỷ lệ loại theo vùng", 6, 6, 9, 6,
     "Singlish dùng lọc WER; paper đánh giá giọng vùng nói WER hạn chế với giọng ít dữ liệu."),
    ("S13", "Đo giọng vùng", "Độ giống giọng vùng + nghe so sánh XAB bởi người bản ngữ + bộ phân loại phương ngữ", 6, 7, 7, 7,
     "ViMD: bộ phân loại giọng Trung chỉ đạt F1 62,5%, nên chỉ làm chỉ báo phụ."),
    ("S14", "Tỷ lệ thật và sinh", "Trộn dữ liệu thật và dữ liệu sinh khoảng 1:1, theo dõi chỗ bão hòa", 7, 7, 8, 6,
     "Versatile TTS: tiếng Hàn 3.700 giờ thật + 4.000 giờ sinh, WER 8,48 → 6,31; thêm nữa gần như không cải thiện."),
    ("H1", "Hướng dữ liệu", "Sinh dữ liệu miền xe bằng TTS thay cho dữ liệu xe thật", 6, 8, 8, 5,
     "Versatile TTS: từ khóa ô tô tiếng Hoa CER 21,32 → 13,15; chưa rõ phần dữ liệu thật có thuộc miền xe không."),
    ("H2", "Hướng dữ liệu", "Trộn giọng thật ngoài miền xe + dữ liệu sinh miền xe", 7, 8, 8, 5,
     "Hai paper về TTS cho ASR đều thử trộn thật + sinh; chưa ai thử chỉ dùng dữ liệu sinh."),
    ("H3", "Hướng dữ liệu", "Thêm tập sinh ngoài miền xe, cùng phân bố câu với tập thật (M3)", 5, 8, 8, 8,
     "Đề xuất của mình; có lý do về logic, chưa paper nào kiểm riêng thiết kế này."),
    ("H4", "Hướng dữ liệu", "Dùng tiếng ồn xe thật (AISHELL-5, CAVEMOVE) thay cho tiếng ồn mô phỏng", 7, 7, 8, 6,
     "Nhiễu giúp (Ogun et al.); nhiễu xe thật tốt hơn nhiễu mô phỏng thì chưa có bằng chứng; giấy phép CC BY-SA cần cân nhắc."),
]
SOLUTIONS_NOTE = [("S11", "Dịch cao độ hoặc đổi giọng để tăng độ phủ F0", "Không nên dùng: Ogun et al. thấy cả hai không hiệu quả (WER tệ hơn 0,8% và 2,2%). Chọn người nói có F0 tự nhiên khác nhau.")]

DIALECT_SCORES = [
    ("Bắc", 6, 7.5, "Giọng chuẩn, dữ liệu nhiều nhất; ít bị kéo lệch."),
    ("Nam", 5, 7, "Thanh hỏi và ngã gộp; có thể bị kéo về giọng chuẩn."),
    ("Trung", 3, 5.5, "Ít dữ liệu nhất, khó nhất với ASR (WER 17,15% ở ViMD); không phải một giọng duy nhất."),
]

# ------------------------------------------------------------------ tài liệu
# (tên, đường dẫn, dùng cho, mức đã đọc)
PAPERS = [
    ("Zero-Shot Text-to-Speech for Vietnamese (PhoAudiobook)", "https://arxiv.org/abs/2506.01322", "941 giờ, 16 kHz, clip 10–20 s; kết quả XTTS-v2, VALL-E, VoiceCraft", "Đã đọc bảng kết quả"),
    ("Singlish, Can or Not? (Chatterbox, CosyVoice 3)", "https://arxiv.org/abs/2607.23027", "Zero-shot mất giọng vùng; tinh chỉnh cải thiện; số liệu giống người nói và giọng vùng", "Đã đọc bảng kết quả"),
    ("Enhancing Low-Resource ASR through Versatile TTS", "https://arxiv.org/abs/2410.16726", "Số người nói, số câu, tỷ lệ thật/sinh; từ khóa ô tô, phương ngữ", "Đã đọc bảng; dữ liệu nội bộ, một mô hình TTS"),
    ("An Exhaustive Evaluation of TTS- and VC-based Data Augmentation for ASR", "https://arxiv.org/abs/2503.08954", "Nhiễu, vang, người nói, cao độ: yếu tố nào giúp ASR", "Đã đọc bảng; tiếng Anh, Glow-TTS"),
    ("Multi-Dialect Vietnamese: ViMD", "https://arxiv.org/html/2410.03458v1", "102,56 giờ, 63 tỉnh; WER theo vùng; giọng Trung khó nhất", "Đã đọc"),
    ("Cross-dialectal perception of Vietnamese tones (Jewell, Yale 2022)", "https://ling.yale.edu/media/227/download", "Khác biệt thanh điệu, phụ âm, từ vựng giữa các vùng", "Đã đọc"),
    ("Vietnamese Speech Command Recognition (VSC_FU)", "https://ftp.saiconference.com/Downloads/Volume10No7/Paper_28-Vietnamese_Speech_Command_Recognition.pdf", "293 người, 3 miền, 15 lệnh, 8 kHz", "Đã đọc"),
    ("AISHELL-5 (OpenSLR 159)", "https://openslr.org/159/", "Khoảng 40 giờ nền ồn trong xe; CC BY-SA 4.0", "Đã đọc trang dữ liệu"),
    ("CAVEMOVE", "https://arxiv.org/abs/2508.19691", "Nhiễu và đáp ứng xung trong xe", "Chỉ đọc tóm tắt; giấy phép chưa rõ"),
    ("VietPrism", "https://arxiv.org/abs/2609.30005", "993 giờ giọng thật, 5 nhóm phương ngữ", "Chỉ đọc tóm tắt; giấy phép chưa rõ"),
    ("SmartNLU (Interspeech 2022)", "https://www.isca-archive.org/interspeech_2022/nguyen22c_interspeech.html", "Văn bản nhà thông minh tiếng Việt", "Chỉ đọc tóm tắt; chưa rõ có âm thanh"),
    ("Accent Analogy Guidance", "https://arxiv.org/abs/2609.29123", "Đánh đổi giữa độ giống người nói và giọng", "Chỉ đọc tóm tắt"),
    ("Activation Steering for Accent-Neutralized Zero-Shot TTS", "https://arxiv.org/abs/2603.05977", "Điều hướng giọng", "Chỉ đọc tóm tắt"),
    ("Accent Vector", "https://arxiv.org/abs/2603.07534", "Điều khiển giọng không cần dữ liệu giọng", "Chỉ đọc tóm tắt"),
    ("CLARITY", "https://www.alphaxiv.org/abs/2511.11104", "Viết lại text và dùng đoạn tham chiếu cùng giọng", "Chỉ đọc tóm tắt"),
    ("Pairwise Evaluation of Accent Similarity in Speech Synthesis", "https://arxiv.org/abs/2505.14410", "WER hạn chế với giọng ít dữ liệu; cách đo giọng vùng", "Chỉ đọc tóm tắt"),
    ("Evaluating and reducing the distance between synthetic and real speech", "https://arxiv.org/abs/2211.16049", "Khoảng cách phân bố thật và sinh", "Chỉ đọc tóm tắt"),
    ("Zero-Shot TTS With Enhanced Audio Prompts (WildSpoof)", "https://arxiv.org/abs/2602.05770", "Làm sạch đoạn tham chiếu", "Chỉ đọc tóm tắt"),
    ("Synthesizing the Lombard Effect in TTS", "https://arxiv.org/abs/2606.23176", "TTS mô phỏng hiệu ứng Lombard", "Chỉ đọc tóm tắt"),
]
