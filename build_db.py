"""
Rebuilds regtech_cyber.db from scratch using schema.sql plus the four
source JSON files (risks.json, innovations.json, mitigations.json,
barriers.json). Safe to re-run any time one of those files changes --
it deletes any existing regtech_cyber.db first and recreates it clean.

Usage:
    python build_db.py
"""
import sqlite3, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "regtech_cyber.db")

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
conn.executescript(open(os.path.join(HERE, "schema.sql")).read())

risks = json.load(open(os.path.join(HERE, "risks.json")))
innovations = json.load(open(os.path.join(HERE, "innovations.json")))
mitigations = json.load(open(os.path.join(HERE, "mitigations.json")))
barriers = json.load(open(os.path.join(HERE, "barriers.json")))

for r in risks:
    conn.execute("INSERT INTO risk (risk_code, name, description, category, source_chapter) VALUES (?,?,?,?,?)",
        (r["risk_id"], r["name"], r["description"], r["category"], r["source_chapter"]))

for i in innovations:
    conn.execute("""INSERT INTO innovation
        (innovation_code, name, technique_category, description, quantified_result, dual_use_flag, dual_use_note, source_chapter)
        VALUES (?,?,?,?,?,?,?,?)""",
        (i["innovation_id"], i["name"], i["technique_category"], i["description"], i.get("quantified_result"),
         1 if i.get("dual_use_flag") else 0, i.get("dual_use_note"), i["source_chapter"]))

for m in mitigations:
    conn.execute("""INSERT INTO mitigation
        (mitigation_code, name, description, category, maturity_level, source_chapter)
        VALUES (?,?,?,?,?,?)""",
        (m["mitigation_id"], m["name"], m.get("comments"), "process/legislative", m["maturity_level"], m["source_chapter"]))

for b in barriers:
    conn.execute("INSERT INTO mitigation_barrier (barrier_code, description) VALUES (?,?)",
        (b["barrier_id"], b["description"]))

conn.commit()

risk_id  = dict(conn.execute("SELECT risk_code, id FROM risk"))
innov_id = dict(conn.execute("SELECT innovation_code, id FROM innovation"))
mit_id   = dict(conn.execute("SELECT mitigation_code, id FROM mitigation"))

for i in innovations:
    for rcode in i.get("related_risk_ids", []):
        conn.execute("INSERT OR IGNORE INTO risk_innovation (risk_id, innovation_id) VALUES (?,?)",
            (risk_id[rcode], innov_id[i["innovation_id"]]))

for m in mitigations:
    for rcode in m.get("related_risk_ids", []):
        conn.execute("""INSERT OR IGNORE INTO risk_mitigation
            (risk_id, mitigation_id, mitigation_status, contingency_status, comments) VALUES (?,?,?,?,?)""",
            (risk_id[rcode], mit_id[m["mitigation_id"]], m.get("mitigation_status"), m.get("contingency_status"), m.get("comments")))

conn.commit()

all_refs = set()
for coll in (risks, innovations, mitigations, barriers):
    for row in coll:
        all_refs.update(row.get("source_refs", []))
for ref in sorted(all_refs):
    conn.execute("INSERT OR IGNORE INTO source (ref_number) VALUES (?)", (ref,))
conn.commit()
src_id = dict(conn.execute("SELECT ref_number, id FROM source"))

for r in risks:
    for ref in r.get("source_refs", []):
        conn.execute("INSERT OR IGNORE INTO risk_source (risk_id, source_id) VALUES (?,?)", (risk_id[r["risk_id"]], src_id[ref]))
for i in innovations:
    for ref in i.get("source_refs", []):
        conn.execute("INSERT OR IGNORE INTO innovation_source (innovation_id, source_id) VALUES (?,?)", (innov_id[i["innovation_id"]], src_id[ref]))
for m in mitigations:
    for ref in m.get("source_refs", []):
        conn.execute("INSERT OR IGNORE INTO mitigation_source (mitigation_id, source_id) VALUES (?,?)", (mit_id[m["mitigation_id"]], src_id[ref]))

conn.commit()

print("Rebuilt regtech_cyber.db")
for t in ["risk","innovation","mitigation","mitigation_barrier","regulation","sector","source"]:
    n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"  {t:22s} {n} rows")

conn.close()
