ARTIFACT_MARKDOWN = "01_鍏ㄩ噺鑴辨按搴曠.md"
ARTIFACT_TABLES = "02_鐮旀姤鍏ㄩ噺缁撴瀯鍖栨暟鎹?xlsx"
ARTIFACT_RAW_TABLES = "02A_鐮旀姤鍘熷琛ㄦ牸璧勪骇.xlsx"
ARTIFACT_SUMMARY = "03_鎶曠爺缁撹绮惧崕.xlsx"
ARTIFACT_CLASSIFICATION = "04_琛ㄦ牸鍒嗙被缁撴灉.xlsx"
ARTIFACT_FINANCIALS = "05_鏍稿績璐㈠姟鎸囨爣鏍囧噯鍖?xlsx"
ARTIFACT_MERGE_DIAGNOSTICS = "06_pdfplumber_merge_diagnostics.xlsx"
ARTIFACT_PDFPLUMBER_PROFILE_DIAGNOSTICS = "06A_pdfplumber_profile_diagnostics.xlsx"
ARTIFACT_SEGMENT_MAP = "07_table_segment_map.xlsx"
ARTIFACT_GLUED_SPLIT_DIAGNOSTICS = "07A_glued_table_split_diagnostics.xlsx"
ARTIFACT_BATCH_STATUS = "09_batch_run_status.xlsx"

__all__ = [name for name in globals() if name.startswith("ARTIFACT_")]
