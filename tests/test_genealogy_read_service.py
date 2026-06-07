from services.genealogy_read_service import (
    NGUYEN_PHUOC_LINEAGE_KEYWORDS,
    belongs_to_nguyen_phuoc_lineage,
)


def test_nguyen_phuoc_lineage_keywords_cover_expected_terms():
    assert NGUYEN_PHUOC_LINEAGE_KEYWORDS == (
        'Vua',
        'Miên',
        'Hồng',
        'Hường',
        'Ưng',
        'Bửu',
        'Vĩnh',
        'Bảo',
        'Quý',
        'Nguyễn Phước',
        'Nguyễn Phúc',
    )


def test_belongs_to_nguyen_phuoc_lineage_matches_keyword_presence():
    assert belongs_to_nguyen_phuoc_lineage('Nguyễn Phước Bảo Long') is True
    assert belongs_to_nguyen_phuoc_lineage('Trần Văn A') is False
    assert belongs_to_nguyen_phuoc_lineage('') is False
