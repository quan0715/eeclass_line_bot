import pytest
from eeclass_line_bot.models import ChatStatus


@pytest.mark.django_db
def test_ChatStatus_get_or_create():
    status, exist = ChatStatus.objects.get_or_create(line_user_id="test_id", status='test_status', propagation=True)
    assert status.line_user_id=='test_id'
    if not exist:
        assert status.status=='test_status'
        assert status.propagation==True

@pytest.mark.django_db
def test_ChatStatus_delete():
    status, exist = ChatStatus.objects.get_or_create(line_user_id="test_id", status='test_status', propagation=True)
    status.delete()
    assert len(ChatStatus.objects.filter(line_user_id='test_id'))==0

@pytest.mark.django_db
def test_ChatStatus_modify():
    status, created = ChatStatus.objects.get_or_create(line_user_id="test_id")
    status.delete()
    status, created = ChatStatus.objects.get_or_create(line_user_id="test_id", status='test_status', propagation=True)
    assert status.line_user_id=='test_id'
    assert status.status=='test_status'
    assert status.propagation==True
    status.status='modified_status'
    status.propagation=False
    status.save()
    reget_status, created = ChatStatus.objects.get_or_create(line_user_id="test_id")
    assert not created
    assert reget_status.line_user_id=='test_id'
    assert reget_status.status=='modified_status'
    assert reget_status.propagation==False
