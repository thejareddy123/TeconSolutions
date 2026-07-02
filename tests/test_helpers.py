import pytest
from app.utils.helpers import generate_employee_id,allowed_document_types,hash_password,verify_password


def test_generate_employee_id_1():
    assert generate_employee_id(0) == "EMP001"

def test_generate_employee_id_2():
    assert generate_employee_id(5) == "EMP006"
    assert generate_employee_id(11) == "EMP012"

def test_generate_employee_id_3():
    assert generate_employee_id(99) == "EMP100"




@pytest.mark.parametrize(
    "filename, expected",
    [
        ("resume.pdf", True),
        ("resume.docx", True),
        ("notes.txt", True),
        ("virus.exe", False),
        ("photo.png", False),
    ],
)
def test_allowed_document_types(filename, expected):
    assert allowed_document_types(filename) == expected



def test_correct_password():
    hashed = hash_password("Admin@123")
    assert verify_password("Admin@123", hashed)

def test_wrong_password():
    hashed = hash_password("Admin@123")
    assert not verify_password("Wrong", hashed)

def test_empty_password():
    hashed = hash_password("Admin@123")
    assert  not verify_password("", hashed)

def test_correct_password(hashed_password):
    assert verify_password("Admin@123", hashed_password)

def test_wrong_password(hashed_password):
    assert not verify_password("WrongPassword", hashed_password)