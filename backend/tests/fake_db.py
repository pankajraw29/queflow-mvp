"""Minimal in-memory stand-in for Motor's database/collections.

Implements only the operations the app uses, so the full HTTP test-suite
can run without a real MongoDB server.
"""
from bson import ObjectId


class FakeCursor:
    def __init__(self, docs):
        self._docs = list(docs)

    def sort(self, key, direction=1):
        self._docs = sorted(
            self._docs, key=lambda d: d.get(key), reverse=(direction < 0)
        )
        return self

    async def to_list(self, length=None):
        if length is None:
            return list(self._docs)
        return self._docs[:length]


def _match(doc, filt):
    for key, cond in filt.items():
        value = doc.get(key)
        if isinstance(cond, dict):
            for op, operand in cond.items():
                if op == "$in":
                    if value not in operand:
                        return False
                elif op == "$lt":
                    if not (value < operand):
                        return False
                elif op == "$lte":
                    if not (value <= operand):
                        return False
                elif op == "$gte":
                    if not (value >= operand):
                        return False
                elif op == "$ne":
                    if value == operand:
                        return False
                else:
                    raise ValueError(f"unsupported operator {op}")
        else:
            if value != cond:
                return False
    return True


class _Result:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class FakeCollection:
    def __init__(self):
        self.docs = []

    async def insert_one(self, doc):
        doc = dict(doc)
        doc.setdefault("_id", ObjectId())
        self.docs.append(doc)
        return _Result(inserted_id=doc["_id"])

    async def find_one(self, filt):
        for d in self.docs:
            if _match(d, filt):
                return d
        return None

    def find(self, filt=None):
        return FakeCursor([d for d in self.docs if _match(d, filt or {})])

    def _apply(self, doc, update):
        for op, fields in update.items():
            if op == "$set":
                doc.update(fields)
            elif op == "$inc":
                for k, v in fields.items():
                    doc[k] = doc.get(k, 0) + v
            else:
                raise ValueError(f"unsupported update {op}")

    async def update_one(self, filt, update):
        doc = await self.find_one(filt)
        if doc is None:
            return _Result(matched_count=0, modified_count=0)
        self._apply(doc, update)
        return _Result(matched_count=1, modified_count=1)

    async def find_one_and_update(self, filt, update, upsert=False, return_document=None):
        doc = await self.find_one(filt)
        if doc is None and upsert:
            doc = dict(filt)
            doc.setdefault("_id", ObjectId())
            self.docs.append(doc)
        if doc is not None:
            self._apply(doc, update)
        return doc  # callers always want the AFTER document

    async def delete_one(self, filt):
        doc = await self.find_one(filt)
        if doc is not None:
            self.docs.remove(doc)
        return _Result(deleted_count=1 if doc else 0)

    async def delete_many(self, filt):
        before = len(self.docs)
        self.docs = [d for d in self.docs if not _match(d, filt)]
        return _Result(deleted_count=before - len(self.docs))

    async def count_documents(self, filt):
        return sum(1 for d in self.docs if _match(d, filt))


class FakeDB:
    def __init__(self):
        self.businesses = FakeCollection()
        self.queues = FakeCollection()
        self.tickets = FakeCollection()
        self.counters = FakeCollection()
