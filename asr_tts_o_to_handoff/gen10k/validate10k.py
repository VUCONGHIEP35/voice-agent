# -*- coding: utf-8 -*-
"""Kiểm độc lập bộ dữ liệu đã sinh (chỉ đọc thư mục đầu ra).

Chạy: py -3.13 validate10k.py [../data/m1m2_10k]
Ghi qa_report.json vào thư mục dữ liệu; mã thoát 1 nếu có lỗi.
"""
import collections, glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
D = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(HERE), "data", "m1m2_10k")

REQUIRED = {"sample_id": str, "purpose": str, "case_id": str, "intent": str, "intent_id": str, "speech_act": str, "text_raw": str,
            "text_spoken": str, "language_mix": str, "norm_features": list, "lexicon_variant": str, "speaker_region": str,
            "speaker_state": str, "factors_covered": list, "n_syllables": int, "length_class": str, "review_status": str,
            "review_reasons": list, "regional_words": list, "synthetic_address": bool, "admin_name_pre2025": bool, "has_wake": bool,
            "sub_region": str, "residence": str, "vocab_source": str, "frame_id": str, "frame": str, "frame_source": str, "evidence": str, "source_ids": list, "slots": list, "notes": str,
            # v3 (CHANGES_v3 C5, C6)
            "core": str, "core_cap": str, "app_group": str, "platform": str, "pron_variant": str}
PLATFORMS = {"oem_vinfast", "android_head_unit", "phone_projection", "any"}
APP_SRC = "K1 app"
APP_G14_MAX_SHARE = 0.35        # G1–G4 tối đa 35% hạn ngạch CS04 khi chưa có quyết định tăng (CHANGES_v3 mục 6, 9)
CORE_DROP_MAX = 0.02            # câu không thuộc G: tỷ lệ lõi/câu (carrier) mỗi case không giảm quá 0,02 so với v2 (người dùng 2026-10-15)
MIN_APP_CORE_RATIO = 0.5        # câu G: tỷ lệ lõi/câu theo carrier_cap >= 0,5
BASELINE_V2 = os.path.join(os.path.dirname(HERE), "data", "m1m2_10k_v2", "diversity_report.json")   # chỉ đọc
STEP1 = ["S23", "S51", "S52", "S53", "S54", "S55", "D01", "D03", "E02", "E03", "E04", "E05", "E06", "E07", "E08"]
STEP1_SECONDARY = ["S33", "S34"]
MIN_PER_FACTOR = 50
MIN_CORE_RATIO = 0.5   # góp ý v1 mục 2 (ngưỡng đề xuất, chưa có bài báo kiểm)
W, E = r"(?<![\wÀ-ỹ])", r"(?![\wÀ-ỹ])"
NOT_IN = {  # tiểu từ/từ không được xuất hiện trong text_raw của vùng
    "Bắc": ["nha", "nghen", "rứa", "chừ", "tui", "giùm", "dùm", "hông", "mạ", "kiếng", "quẹo", "máy lạnh", "đậu xe", "kẹt xe"],
    "Nam": ["rứa", "chừ", "mạ", "vâng", "nhé", "hộ tôi", "tắc đường", "vòng xuyến"],
    "Trung": ["nghen", "hộ tôi", "tía", "nhỉ", "dùm"],
}
NOT_IN["Trung-HN"] = [w for w in NOT_IN["Bắc"] if w != "mạ"]
NOT_IN["Trung-HCM"] = [w for w in NOT_IN["Nam"] if w != "mạ"] + ["nghen", "dùm"]
NOT_IN["Trung-Quê"] = ["nghen", "hộ tôi", "tía", "nhỉ", "dùm", "hen", "chừ", "nha", "giùm"]
NUM_NOT_IN = {"Bắc": ["ngàn", "lẻ"], "Trung": ["nghìn", "linh"], "Nam": ["nghìn", "linh"]}
DUP_RE = re.compile(r"(?<![\wÀ-ỹ])([\wÀ-ỹ]{2,})\s+((?i:\1))(?![\wÀ-ỹ])")


def profile_key(r):
    if r["speaker_region"] != "Trung":
        return r["speaker_region"]
    return {"Hà Nội": "Trung-HN", "TP.HCM": "Trung-HCM"}.get(r.get("residence", "Quê"), "Trung-Quê")


def key(t):
    t = t.lower()
    t = re.sub(r"[\.,;:!?\"“”()\[\]–-]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def main():
    errors, warns = [], []
    man = json.load(open(os.path.join(D, "manifest.json"), encoding="utf-8"))
    rows, file_of = [], {}
    for fi in man["files"]:
        p = os.path.join(D, fi["file"])
        lines = [json.loads(l) for l in open(p, encoding="utf-8")]
        if len(lines) != fi["n"]:
            errors.append(f"{fi['file']}: số dòng {len(lines)} khác manifest {fi['n']}")
        for r in lines:
            if r["case_id"] not in fi["cases"]:
                errors.append(f"{fi['file']}: {r['sample_id']} thuộc {r['case_id']} không đúng nhóm")
            file_of[r["sample_id"]] = fi["file"]
        rows += lines
    extra = set(os.path.basename(p) for p in glob.glob(os.path.join(D, "*.jsonl"))) - {f["file"] for f in man["files"]}
    if extra:
        errors.append(f"file JSONL ngoài manifest: {sorted(extra)}")

    # 1. lược đồ
    for r in rows:
        for k, t in REQUIRED.items():
            if k not in r or not isinstance(r[k], t):
                errors.append(f"{r.get('sample_id')}: thiếu/sai kiểu trường {k}")
    ids = [r["sample_id"] for r in rows]
    if len(ids) != len(set(ids)):
        errors.append("sample_id bị trùng")

    # 2. hạn ngạch
    cnt = collections.Counter(r["case_id"] for r in rows)
    for c, q in man["quota"].items():
        if cnt[c] != q:
            gen = man.get("per_case", {}).get(c, {}).get("generated")
            if gen == cnt[c]:
                warns.append(f"{c}: {cnt[c]}/{q} câu (thiếu {q - cnt[c]}, bộ sinh đã báo trong manifest)")
            else:
                errors.append(f"{c}: {cnt[c]} câu, hạn ngạch {q}")
    total_target = sum(man["quota"].values())

    # 3. trùng
    kr = collections.Counter(key(r["text_raw"]) for r in rows)
    ks = collections.Counter(key(r["text_spoken"]) for r in rows)
    dup_raw = [k for k, v in kr.items() if v > 1]
    dup_sp = [k for k, v in ks.items() if v > 1]
    if dup_raw or dup_sp:
        errors.append(f"câu trùng: text_raw {len(dup_raw)}, text_spoken {len(dup_sp)} (vd: {(dup_raw + dup_sp)[:3]})")

    # 4. text_spoken
    for r in rows:
        sp = r["text_spoken"]
        if re.search(r"\d", sp):
            errors.append(f"{r['sample_id']}: còn chữ số trong text_spoken: {sp}")
        if re.search(r"[%°/]|km/h|MHz|kWh", sp):
            errors.append(f"{r['sample_id']}: còn ký hiệu trong text_spoken: {sp}")
        n = len(re.sub(r"[\.,;:!?–]", " ", sp).split())
        if n != r["n_syllables"]:
            errors.append(f"{r['sample_id']}: n_syllables {r['n_syllables']} khác đếm {n}")
        end = {"Câu hỏi": "?", "Kêu cứu": "!"}.get(r["speech_act"], ".")
        if not r["text_raw"].endswith(end) or not sp.endswith(end):
            errors.append(f"{r['sample_id']}: dấu câu cuối không khớp loại câu")
        if r["text_raw"][:1] != r["text_raw"][:1].upper():
            warns.append(f"{r['sample_id']}: text_raw không viết hoa đầu câu")
        # cách đọc số theo vùng
        raw_words = set(re.findall(r"[\wÀ-ỹ]+", r["text_raw"]))
        for w in NUM_NOT_IN[r["speaker_region"]]:
            if re.search(W + w + E, sp) and w not in raw_words:
                errors.append(f"{r['sample_id']}: đọc số sai vùng ({w}) ở giọng {r['speaker_region']}: {sp}")
        for m in DUP_RE.finditer(r["text_raw"]):
            if not (m.group(1).islower() and m.group(2)[:1].isupper()):   # 'anh Anh' là hợp lệ
                errors.append(f"{r['sample_id']}: lặp từ liền nhau '{m.group(0)}': {r['text_raw']}")
        if re.search(r"\b(ABS|ATM|USB|VOV|VOH|FM|MHz|GPS|AQI|USD|VND|BOT|EDM|ODO)\b", sp):
            errors.append(f"{r['sample_id']}: viết tắt chưa đọc ra trong text_spoken: {sp}")
        raw_lc_first = r["text_raw"][:1].lower() + r["text_raw"][1:]   # giữ hoa của tên riêng (Nha Trang)
        prof = profile_key(r)
        for w in NOT_IN[prof] + (["tui"] if prof == "Trung-Quê" and r.get("sub_region") not in (None, "Huế") else []):
            # bỏ qua khi từ là phần đầu của tên riêng (Nha Trang): từ sau viết hoa
            def next_upper(m):
                nx = re.match(r"\s+(\S)", r["text_raw"][m.end():])
                return bool(nx) and nx.group(1).isupper()
            if any(not next_upper(m) for m in re.finditer(W + re.escape(w) + E, raw_lc_first)):
                errors.append(f"{r['sample_id']}: từ '{w}' không hợp hồ sơ {prof}: {r['text_raw']}")

    # 5. cân bằng vùng
    reg = collections.defaultdict(collections.Counter)
    for r in rows:
        reg[r["case_id"]][r["speaker_region"]] += 1
        if r["lexicon_variant"] != r.get("vocab_source", r["lexicon_variant"]):
            errors.append(f"{r['sample_id']}: lexicon_variant khác vocab_source")
        if r["speaker_region"] in ("Bắc", "Nam") and r.get("vocab_source", r["speaker_region"]) != r["speaker_region"]:
            errors.append(f"{r['sample_id']}: giọng {r['speaker_region']} nhưng từ vựng {r['vocab_source']}")
    for c, cc in reg.items():
        vals = [cc[x] for x in ("Bắc", "Trung", "Nam")]
        if max(vals) - min(vals) > 1:
            if cnt[c] < man["quota"].get(c, 0):
                warns.append(f"{c}: lệch vùng {dict(cc)} (case thiếu câu)")
            else:
                errors.append(f"{c}: lệch vùng {dict(cc)}")

    # 6. review
    for r in rows:
        if r["speaker_region"] == "Trung" and r["review_status"] != "cần duyệt":
            errors.append(f"{r['sample_id']}: câu miền Trung chưa gắn 'cần duyệt'")
        if r["review_status"] != "không bắt buộc" and not r["review_reasons"]:
            errors.append(f"{r['sample_id']}: review_status {r['review_status']} nhưng không có lý do")
        if r["review_status"] == "không bắt buộc" and r["review_reasons"]:
            errors.append(f"{r['sample_id']}: có lý do duyệt nhưng review_status 'không bắt buộc'")
    # 7. địa chỉ tổng hợp
    addr_pat = re.compile(r"(số \d+[A-D]?\b|\b(ngõ|hẻm|kiệt|ngách) \d+|\b\d+/\d+ (đường|phố))")
    for r in rows:
        if addr_pat.search(r["text_raw"]) and not r["synthetic_address"] and "{addr}" not in r["frame"]:
            if re.search(r"\{(addr|so_nha)\}", r["frame"]) or re.search(r"(ngõ|hẻm|kiệt|ngách) \d+", r["text_raw"]):
                errors.append(f"{r['sample_id']}: có địa chỉ nhưng synthetic_address=false")
    # 8. tỷ trọng khung
    fr = collections.defaultdict(collections.Counter)
    for r in rows:
        fr[r["case_id"]][r["frame_id"]] += 1
    frame_share = {}
    for c, cc in fr.items():
        fid, m = cc.most_common(1)[0]
        share = m / man["quota"][c]
        frame_share[c] = dict(max_frame=fid, n=m, share=round(share, 4), frames_used=len(cc))
        if share > 0.05:
            errors.append(f"{c}: khung {fid} chiếm {share:.1%} (> 5%)")
    top_global = max((v, k) for cc in fr.values() for k, v in cc.items())
    if top_global[0] / len(rows) > 0.01:
        errors.append(f"khung {top_global[1]} chiếm {top_global[0] / len(rows):.2%} toàn bộ (> 1%)")
    # 9. phủ yếu tố bước 1
    fac = collections.Counter(f for r in rows for f in r["factors_covered"])
    for f in STEP1 + STEP1_SECONDARY:
        if fac[f] < MIN_PER_FACTOR:
            errors.append(f"yếu tố {f} chỉ phủ {fac[f]} câu (< {MIN_PER_FACTOR})")
    # 9b. lõi câu: tỷ lệ lõi/câu theo carrier (cùng hàm với diversity10k), cảnh báo khi < 0,5;
    #     trần câu/lõi kiểm theo carrier_cap (v3: giữ tên app, bản đồ, thu phí), lỗi khi một lõi vượt trần của bộ sinh
    core_ratio, core_max = {}, 0
    try:
        sys.path.insert(0, HERE)
        import diversity10k as DV
        masks = DV.build_masks()
        cores = [DV.carrier(r["text_raw"], masks)[1] for r in rows]
        cc_all = collections.Counter(cores)
        keep = DV.build_keep()
        cap_cores = [DV.carrier_cap(r["text_raw"], masks, keep)[1] for r in rows]
        cc_cap = collections.Counter(cap_cores)
        core_max = max(cc_cap.values())
        cap = 3
        m = re.search(r"tối đa (\d+) câu", man.get("rules", {}).get("core_cap", ""))
        if m:
            cap = int(m.group(1))
            if core_max > cap:
                errors.append(f"có lõi (carrier_cap) xuất hiện {core_max} lần (> trần {cap}): {cc_cap.most_common(1)[0][0]}")
        for c in sorted(cnt):
            cs = [k for k, r in zip(cores, rows) if r["case_id"] == c]
            core_ratio[c] = round(len(set(cs)) / len(cs), 3)
            if core_ratio[c] < MIN_CORE_RATIO:
                warns.append(f"{c}: tỷ lệ lõi/câu {core_ratio[c]} < {MIN_CORE_RATIO}")
        core_total = round(len(cc_all) / len(rows), 3)
    except Exception as e:  # noqa
        warns.append(f"không tính được lõi: {e}")
        core_total = None
        cores = cap_cores = None
    # 9c. v3: trường lõi, nhóm app, platform, cách đọc từ ngoại
    if cores is not None:
        for r, k, kc in zip(rows, cores, cap_cores):
            if r.get("core") != k or r.get("core_cap") != kc:
                errors.append(f"{r['sample_id']}: core/core_cap khác carrier/carrier_cap tính lại")
    for r in rows:
        if r.get("platform") not in PLATFORMS:
            errors.append(f"{r['sample_id']}: platform không hợp lệ: {r.get('platform')}")
        is_app = r.get("frame_source") == APP_SRC
        if is_app != bool(r.get("app_group")):
            errors.append(f"{r['sample_id']}: app_group '{r.get('app_group')}' không khớp frame_source '{r.get('frame_source')}'")
        if is_app and r["review_status"] != "cần duyệt":
            errors.append(f"{r['sample_id']}: câu khung app chưa gắn 'cần duyệt'")
        if is_app and r["evidence"] != "constructed":
            errors.append(f"{r['sample_id']}: câu khung app có evidence {r['evidence']}")
    app_groups, app_core_ratio, core_ratio_nonapp, core_drop = {}, {}, {}, {}
    try:
        import frames_app10k as FA
        gcount = collections.Counter(r["app_group"] for r in rows if r.get("app_group"))
        for g, t in sorted(FA.GROUP_TARGET.items()):
            app_groups[g] = dict(target=t, n=gcount[g])
            if gcount[g] > t:
                errors.append(f"nhóm {g}: {gcount[g]} câu, vượt mục tiêu {t}")
            elif gcount[g] < t:
                warns.append(f"nhóm {g}: {gcount[g]}/{t} câu (thiếu khung, giữ ít hơn)")
        g14 = sum(1 for r in rows if r.get("app_group") in ("G1", "G2", "G3", "G4"))
        lim = APP_G14_MAX_SHARE * man["quota"].get("CS04", 0)
        if g14 > lim:
            errors.append(f"G1–G4 có {g14} câu, vượt {APP_G14_MAX_SHARE:.0%} hạn ngạch CS04 ({lim:.0f})")
        if cap_cores is not None:
            for g in sorted(gcount):
                ks = [kc for kc, r in zip(cap_cores, rows) if r.get("app_group") == g]
                app_core_ratio[g] = round(len(set(ks)) / len(ks), 3)
                if app_core_ratio[g] < MIN_APP_CORE_RATIO:
                    errors.append(f"nhóm {g}: tỷ lệ lõi/câu (carrier_cap) {app_core_ratio[g]} < {MIN_APP_CORE_RATIO}")
            base = {}
            if os.path.exists(BASELINE_V2):
                base = {c: v["ty_le"] for c, v in json.load(open(BASELINE_V2, encoding="utf-8"))["C_khung_mang"]["theo_case"].items()}
            else:
                warns.append(f"không có số gốc v2 ({BASELINE_V2}), bỏ qua so tỷ lệ lõi")
            for c in sorted(cnt):
                ks = [k for k, r in zip(cores, rows) if r["case_id"] == c and not r.get("app_group")]
                core_ratio_nonapp[c] = round(len(set(ks)) / len(ks), 3)
                if c in base:
                    core_drop[c] = round(len(set(ks)) / len(ks) - base[c], 3)
                    if core_drop[c] < -CORE_DROP_MAX - 1e-9:
                        errors.append(f"{c}: tỷ lệ lõi/câu (carrier, câu không thuộc G) {core_ratio_nonapp[c]} giảm {-core_drop[c]} so với v2 {base[c]}")
    except ImportError as e:
        warns.append(f"không kiểm được nhóm app: {e}")
    loan_must = loan_should = 0
    try:
        import loanwords10k as LW
        for r in rows:
            reasons = set(r["review_reasons"])
            taken = []
            for e in LW.ENTRIES:
                for m in e["pat"].finditer(r["text_raw"]):
                    if any(a < m.end() and m.start() < b for a, b in taken):
                        continue
                    taken.append((m.start(), m.end()))
                    col = e["cols"][r["speaker_region"]]
                    if col:
                        if re.search(r"[1-3]", col) and not any(p.startswith(e["id"] + "-") for p in r["pron_variant"].split(",")):
                            warns.append(f"{r['sample_id']}: {e['term']} đã duyệt nhưng không có pron_variant (có thể không tìm thấy để thay)")
                        continue
                    need = (LW.FLAG_SHOULD if e["level"] == "should" else LW.FLAG_MUST).format(e["term"])
                    if need not in reasons:
                        errors.append(f"{r['sample_id']}: thiếu cờ '{need}'")
                    if e["level"] == "must" and r["review_status"] != "cần duyệt":
                        errors.append(f"{r['sample_id']}: có '{e['term']}' chưa duyệt cách đọc nhưng review_status {r['review_status']}")
            loan_must += any(x.startswith("cách đọc chưa xác minh") for x in reasons)
            loan_should += any(x.startswith("cách đọc từ ngoại đã đổi chữ") for x in reasons)
    except ImportError as e:
        warns.append(f"không kiểm được bảng từ ngoại: {e}")
    # 10. mục đích
    for r in rows:
        if r["purpose"] == "M2" and r["case_id"] != "CS12":
            warns.append(f"{r['sample_id']}: M2 ngoài CS12")
        if r["purpose"] not in ("M1", "M2"):
            errors.append(f"{r['sample_id']}: purpose {r['purpose']}")

    summary = dict(
        total=len(rows), target=total_target, per_case=dict(sorted(cnt.items())),
        region=dict(collections.Counter(r["speaker_region"] for r in rows)),
        vocab_source=dict(collections.Counter(r.get("vocab_source") for r in rows)),
        trung_residence=dict(collections.Counter(r.get("residence") for r in rows if r["speaker_region"] == "Trung")),
        trung_sub_region=dict(collections.Counter(r.get("sub_region") for r in rows if r["speaker_region"] == "Trung")),
        region_per_case={c: dict(v) for c, v in sorted(reg.items())},
        purpose=dict(collections.Counter(r["purpose"] for r in rows)),
        speech_act=dict(collections.Counter(r["speech_act"] for r in rows)),
        length_class=dict(collections.Counter(r["length_class"] for r in rows)),
        language_mix=dict(collections.Counter(r["language_mix"] for r in rows)),
        speaker_state=dict(collections.Counter(r["speaker_state"] for r in rows)),
        review_status=dict(collections.Counter(r["review_status"] for r in rows)),
        review_status_by_region={g: dict(collections.Counter(r["review_status"] for r in rows if r["speaker_region"] == g))
                                 for g in ("Bắc", "Trung", "Nam")},
        evidence=dict(collections.Counter(r["evidence"] for r in rows)),
        frame_source=dict(collections.Counter(r["frame_source"].split(":")[0] if r["frame_source"].startswith("src_commands")
                                              else r["frame_source"] for r in rows)),
        synthetic_address=sum(r["synthetic_address"] for r in rows), admin_name_pre2025=sum(r["admin_name_pre2025"] for r in rows),
        has_wake=sum(r["has_wake"] for r in rows),
        factors_step1={f: fac[f] for f in STEP1 + STEP1_SECONDARY}, factors_all=dict(sorted(fac.items())),
        frame_share=frame_share, distinct_frames=len({r["frame_id"] for r in rows}),
        core_ratio_total=core_total, core_ratio_per_case=core_ratio, core_max_count=core_max,
        core_ratio_nonapp_per_case=core_ratio_nonapp, core_ratio_nonapp_minus_v2=core_drop,
        app_groups=app_groups, app_core_ratio_cap=app_core_ratio,
        platform=dict(collections.Counter(r.get("platform") for r in rows)),
        loan_flag_can_duyet=loan_must, loan_flag_nen_duyet=loan_should,
        pron_variant_set=sum(1 for r in rows if r.get("pron_variant")),
        syllables=dict(min=min(r["n_syllables"] for r in rows), max=max(r["n_syllables"] for r in rows),
                       mean=round(sum(r["n_syllables"] for r in rows) / len(rows), 2)),
        errors=len(errors), warnings=len(warns),
    )
    rep = dict(summary=summary, errors=errors[:500], warnings=warns[:200])
    json.dump(rep, open(os.path.join(D, "qa_report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    for e in errors[:40]:
        print("LỖI:", e)
    print(f"{len(errors)} lỗi, {len(warns)} cảnh báo")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
