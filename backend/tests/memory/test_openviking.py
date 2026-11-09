from backend.memory.openviking import InMemoryMemoryProvider


def test_memory_isolation():
    mem = InMemoryMemoryProvider()
    mem.store_context("t1", "c1", {"note": "fraud"}, trust_level="UNTRUSTED")

    res = mem.retrieve_context("t1", "c1")
    assert res["trust_level"] == "UNTRUSTED"
    assert mem.retrieve_context("t2", "c1") is None
