import urllib.request
import json

url = 'https://wvbozonxguapddgrbitz.supabase.co/rest/v1/'
headers = {
    'apikey': 'sb_publishable_C-De4bkO-fUjauTg_GGGLg_IMot1AnQ',
    'Authorization': 'Bearer sb_publishable_C-De4bkO-fUjauTg_GGGLg_IMot1AnQ'
}
req = urllib.request.Request(url, headers=headers)
res = urllib.request.urlopen(req)
spec = json.loads(res.read().decode())
definitions = spec.get('definitions', {})

print("=" * 60)
print("LIVE SUPABASE DATABASE SCHEMA INSPECTION REPORT")
print("=" * 60)
for table_name in sorted(definitions.keys()):
    schema = definitions[table_name]
    print(f"\nTABLE: public.{table_name}")
    props = schema.get('properties', {})
    required = schema.get('required', [])
    for col, meta in sorted(props.items()):
        col_type = meta.get('type', meta.get('format', 'unknown'))
        is_req = "NOT NULL" if col in required else "NULLABLE"
        print(f"  • {col.ljust(22)} : {col_type.ljust(12)} [{is_req}]")

print("\n" + "=" * 60)
