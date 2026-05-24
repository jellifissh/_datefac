# Stage7K-Fix AI Connectivity Diagnosis

- api_key_present: True
- base_url_present: True
- model_present: True
- external_api_test_attempted: True
- external_api_test_success: False
- http_status: None
- error_type: CONNECTION_ERROR
- error_summary: HTTPSConnectionPool(host='open.bigmodel.cn', port=443): Max retries exceeded with url: /api/paas/v4/chat/completions (Caused by NewConnectionError("HTTPSConnection(host='open.bigmodel.cn', port=443): Failed to establish a new connection: [WinError 10013] 以一种访问权限不允许的方式做了一个访问套接字的尝试。"))
- recommended_fix: Outbound socket blocked; check firewall/endpoint protection/network policy for provider domain:443.

## Safety
- API key value was never logged.
- Only one lightweight API test was executed at most.
- check_delivery_state_overall_status: PASS