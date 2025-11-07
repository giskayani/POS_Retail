from datetime import datetime
from pymongo import ReturnDocument

class IDGenerator:
    def __init__(self, db):
        self.counters = db["counters"]

    def get_next_id(self, prefix: str):
        today = datetime.now().strftime("%Y%m%d")

        # Ambil data counter yang sesuai prefix
        counter = self.counters.find_one({"_id": prefix})

        # Jika belum ada atau tanggal sudah berganti -> reset sequence
        if not counter or counter.get("date") != today:
            counter = self.counters.find_one_and_update(
                {"_id": prefix},
                {"$set": {"sequence": 1, "date": today}},
                upsert=True,
                return_document=ReturnDocument.AFTER
            )
        else:
            # Jika tanggal sama, increment sequence
            counter = self.counters.find_one_and_update(
                {"_id": prefix},
                {"$inc": {"sequence": 1}},
                return_document=ReturnDocument.AFTER
            )

        # Format akhir: PREFIX-YYYYMMDD-0001
        return f"{prefix.upper()}-{today}-{counter['sequence']:04d}"
