import sys
from pathlib import Path
from app.services.ml_engine import ml_engine, SUPPORTED_DISEASES

print(f"Testing all {len(SUPPORTED_DISEASES)} disease models...")
results = {}
for d in SUPPORTED_DISEASES:
    spec = ml_engine.get_disease_spec(d)
    sample_input = {}
    for f in spec['features']:
        fname = f['name']
        ftype = f.get('type', 'numerical')
        if ftype == 'numerical':
            valid_range = f.get('valid_range', [0, 100])
            min_v = valid_range[0] if valid_range else 0
            max_v = valid_range[1] if valid_range and len(valid_range) > 1 else 100
            sample_input[fname] = (min_v + max_v) / 2.0
        elif ftype == 'binary':
            sample_input[fname] = 0
        elif ftype == 'categorical':
            opts = f.get('categories', ['normal', 'standard'])
            sample_input[fname] = opts[0] if opts else 'normal'

    try:
        res = ml_engine.predict(d, sample_input, model_name='tabicl')
        print(f"  [SUCCESS] {d}: prob={res['raw_probability']}, risk={res['risk_level']}, latency={res['inference_latency_ms']}ms, model={res['model_name']} {res['model_version']}")
        results[d] = 'OK'
    except Exception as e:
        import traceback
        print(f"  [FAILED] {d}: {e}")
        traceback.print_exc()
        results[d] = f"FAILED: {e}"

print("Summary of all 10 models:")
for d, status in results.items():
    print(f"  {d}: {status}")
