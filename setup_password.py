"""Run locally. Paste resulting hash into Streamlit secrets. Never publish plaintext password."""
import getpass
from tph_core import password_hash
p1=getpass.getpass('New site passphrase (minimum 14 characters): ')
p2=getpass.getpass('Repeat passphrase: ')
if p1!=p2 or len(p1)<14:raise SystemExit('Passwords do not match or are too short (14+).')
print('\nAdd this as one secret in Streamlit Community Cloud (keep it private):')
print('TPH_PASSWORD_HASH = "'+password_hash(p1)+'"')
