from app.services.pinecone_service import upsert_record, query_records


def test_listing_upsert_1():
    record_id = upsert_record(
        "2 bed 2 bath apartment in Gainesville near UF, $1450/mo, in-unit laundry, pet friendly.",
        "listing",
        ns="main",
        listing_id="pytest-listing-1",
    )
    assert record_id == "ID-pytest-listing-1"


def test_listing_upsert_2():
    record_id = upsert_record(
        "1 bed 1 bath studio near downtown Gainesville, $1100/mo, parking included, quiet building.",
        "listing",
        ns="main",
        listing_id="pytest-listing-2",
    )
    assert record_id == "ID-pytest-listing-2"


def test_listing_upsert_3():
    record_id = upsert_record(
        "3 bed 2 bath townhouse in Gainesville, $1800/mo, pool, gym, and on bus route to campus.",
        "listing",
        ns="main",
        listing_id="pytest-listing-3",
    )
    assert record_id == "ID-pytest-listing-3"


def test_listing_upsert_4():
    record_id = upsert_record(
        "4 bed 4 bath student apartment near UF, $900/mo per room, furnished, high-speed internet included.",
        "listing",
        ns="main",
        listing_id="pytest-listing-4",
    )
    assert record_id == "ID-pytest-listing-4"


def test_listing_query_1():
    r1 = query_records("pet friendly 2 bed near UF", ns="main", top_k=2)
    assert r1 is not None


def test_listing_query_2():
    r2 = query_records("quiet 1 bed downtown with parking", ns="main", top_k=2)
    assert r2 is not None


def test_user_upsert_1():
    record_id = upsert_record(
        "User wants a 2 bedroom under $1600 near UF with pet-friendly policies and laundry.",
        "profile",
        ns="user_preference",
        user_id="pytest-user-1",
    )
    assert record_id == "ID-pytest-user-1"


def test_user_upsert_2():
    record_id = upsert_record(
        "User prefers a quiet 1 bedroom under $1200 near downtown with parking and no roommates.",
        "profile",
        ns="user_preference",
        user_id="pytest-user-2",
    )
    assert record_id == "ID-pytest-user-2"


def test_user_query_1():
    r1 = query_records("2 bedroom pet friendly near UF", ns="user_preference", top_k=2)
    assert r1 is not None


def test_user_query_2():
    r2 = query_records("quiet 1 bedroom downtown parking", ns="user_preference", top_k=2)
    assert r2 is not None
