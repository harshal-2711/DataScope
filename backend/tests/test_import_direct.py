import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal
from app.services.data_connector_service import DataConnectorService
from app.models.company import Company
from app.models.user import User

db = SessionLocal()
comp = db.query(Company).first()
user = db.query(User).first()
print('Testing direct import with company:', comp.id if comp else None, 'user:', user.id if user else None)

try:
    res = DataConnectorService.import_to_dataset(
        db=db,
        company_id=str(comp.id),
        source_type='google_sheets',
        config={'sheet_url': 'https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit?usp=sharing'},
        connection_name='Direct Test Connection',
        user_id=str(user.id)
    )
    print('SUCCESS IMPORT!')
    print('dataset_id:', res['dataset_id'])
    print('rows:', res['row_count'])
    print('cols:', res['column_count'])
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    db.close()
