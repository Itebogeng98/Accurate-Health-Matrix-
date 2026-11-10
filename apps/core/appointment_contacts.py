"""Email contacts for appointment requests; contact availability is not a free slot."""
from .wellness_data import DOCTORS

TEST_CONTACTS = [
    {'name': 'Itebogeng Sebapu - test contact 1', 'email': 'ie.sebapu@gmail.com', 'is_test': True},
    {'name': 'Itebogeng Sebapu - test contact 2', 'email': 'itebogengeugene@gmail.com', 'is_test': True},
]


def appointment_contacts():
    return TEST_CONTACTS + [dict(doctor, is_test=False) for doctor in DOCTORS if doctor.get('email')]
