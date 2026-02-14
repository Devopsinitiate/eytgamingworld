ven """Quick script to check tournament registration status"""
import sqlite3
from datetime import datetime

# Connect to database
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Find Underground tournament
cursor.execute("""
    SELECT name, slug, status, is_public, registration_start, registration_end,
           max_participants, created_at
    FROM tournaments_tournament
    WHERE name LIKE '%underground%' OR name LIKE '%Underground%'
""")

tournaments = cursor.fetchall()

print(f"\nFound {len(tournaments)} tournament(s):\n")
print("="*100)

for t in tournaments:
    name, slug, status, is_public, reg_start, reg_end, max_part, created = t
    print(f"\nTournament: {name}")
    print(f"  Slug: {slug}")
    print(f"  Status: {status}")
    print(f"  Is Public: {is_public}")
    print(f"  Registration Start: {reg_start}")
    print(f"  Registration End: {reg_end}")
    print(f"  Max Participants: {max_part}")
    print(f"  Created: {created}")
    
    # Count participants
    cursor.execute("SELECT COUNT(*) FROM tournaments_participant WHERE tournament_id = (SELECT id FROM tournaments_tournament WHERE slug = ?)", (slug,))
    count = cursor.fetchone()[0]
    print(f"  Registered Participants: {count}")
    
    # Check current time
    print(f"\n  Current time: {datetime.now()}")
    
    # Analyze registration status
    print("\n  Analysis:")
    if status != 'registration':
        print(f"    ❌ Status is '{status}', should be 'registration'")
    else:
        print(f"    ✓ Status is correct")
        
    if not is_public:
        print(f"    ❌ Tournament is not public")
    else:
        print(f"    ✓ Tournament is public")
        
    if not reg_start:
        print(f"    ⚠ Registration start time not set")
    elif reg_end:
        print(f"    ✓ Registration dates are set")
    
    if max_part and count >= max_part:
        print(f"    ❌ Tournament is full ({count}/{max_part})")
    elif max_part:
        print(f"    ✓ Spots available ({count}/{max_part})")
    
    print("\n" + "="*100)

conn.close()
