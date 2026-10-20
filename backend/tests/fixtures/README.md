# Synthetic test-only fixture

`synthetic_cgmacros.csv` is generated data, not CGMacros data. Its field names are a canonical test schema only and are not evidence of the real PhysioNet columns, units, participant IDs, or observations. Tests may use it to exercise temporal preprocessing/training interfaces; production training rejects every path outside the checksum-verified `data/raw/cgmacros/extracted` tree.

Recreate it with:

```powershell
cd backend
python tests/fixtures/generate_synthetic_fixture.py
```
