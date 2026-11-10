import sys,collections,io
cls = {
 "W-ENC": ("Windows default text encoding (cp1252) when a file is opened without encoding=", ["test_colab_proxy_trust_2705","test_failure_classify","test_mobile_contract","test_mobile_contributors","test_update_contributors","test_voicestudio_branding"]),
 "W-POSIX": ("POSIX shell or tool assumed: `bash` resolves to WSL, ':' PATH separator, no openssl, bash syntax", ["test_electron_transition","test_ios_archive_signing","test_gguf_desktop_bundle","test_gguf_portable_x86_runtime","test_release_signing_notes","COLLECTION"]),
 "W-PATH": ("Windows path or filename rules: separators, forbidden characters, case of .EXE, path containment", ["test_virustotal","test_cla_audit","test_confucius4_sidecar","test_ffmpeg_utils","test_media_tool_missing","test_profile_delete_regression","test_omnivoice_gguf","test_db_backup_concurrent_slots"]),
 "W-NODE": ("Node subprocess scripts run from Python fail on Windows", ["test_setup_rocm_variant","test_setup_windows_rocm"]),
 "IMPORT": ("beartype claw_state circular import (import order under xdist)", ["test_windows_rocm_sdk_integrity","test_text_normalization_routes"]),
 "TIMING": ("Timeouts on the 4-worker laptop run", ["test_probe_dictation","test_probe_engines","test_compile_thread_affinity","test_startup_progress_early_bind"]),
 "OTHER": ("Not yet root-caused", ["test_indextts_speed_3588","test_generation_audio_guard","test_mobile_mp3_source","test_bundled_code_policy","test_xdist_data_dir_isolation"]),
}
def classify(node,msg):
    head=node.split("::")[0]
    mod = head.split(".")[-1] if head else "COLLECTION"
    if mod=="VirusTotalTests": mod="test_virustotal"
    if mod=="test_indextts_sidecar": return "W-ENC" if "UnicodeDecodeError" in msg else "W-PATH"
    for k,(d,mods) in cls.items():
        if mod in mods: return k
    return "UNCLASSIFIED"
cnt=collections.Counter(); out=sys.stdout
out.write("class\tkind\ttest\tmessage\n")
for l in io.TextIOWrapper(sys.stdin.buffer,encoding="utf-8"):
    kind,node,msg=(l.rstrip("\n").split("\t")+["",""])[:3]
    k=classify(node,msg); cnt[k]+=1
    out.write(f"{k}\t{kind}\t{node}\t{msg[:200]}\n")
for k,v in cnt.most_common(): sys.stderr.write(f"{k}\t{v}\t{cls.get(k,('',))[0]}\n")
sys.stderr.write(f"total\t{sum(cnt.values())}\n")
