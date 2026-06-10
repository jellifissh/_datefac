# Skill: Environment Troubleshooting

## Core Split
- use `mineru_new` for MinerU CLI and model loading
- use base / DateFac env for runner, pandas, Excel, and sidecar reporting

## Current Safe Settings
- `PYTHONNOUSERSITE=1`
- `PIP_USER=0`
- `huggingface_hub==0.36.2`
- avoid `huggingface_hub>=1.0` because current `transformers / tokenizers` require `<1.0`

## SSL And Endpoint Controls
- `REQUESTS_CA_BUNDLE`
- `SSL_CERT_FILE`
- `HF_ENDPOINT`
- `HTTP_PROXY`
- `HTTPS_PROXY`
- `ALL_PROXY`

## Known Problems
- user site pollution from `AppData\Roaming\Python\Python312\site-packages`
- missing `urllib3`
- SSL certificate verify failed
- official HuggingFace inaccessible
- mirror inaccessible
- wrong package provenance under mixed envs

## Safe Repair Rules
- do not use `verify=False` as a formal fix
- do not reinstall the entire conda env unless the user explicitly approves
- do not blindly upgrade everything with `pip install -U`
- do not casually delete model cache
- prefer diagnosis before reinstall

## First-Line Debug Steps
1. confirm current env
2. confirm package provenance
3. confirm `huggingface_hub` pin
4. confirm certifi path
5. test official HF
6. test mirror only if official fails

